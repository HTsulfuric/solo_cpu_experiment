# RTCore-V1 Assembly Code Sample
# Optimized Ray-Sphere Intersection Routine

.data
    # Object data structure (aligned for vector loads)
    .align 8
    sphere_center:  .double 0.0, 0.0, 100.0    # xyz coordinates
    sphere_radius:  .double 20.0
    sphere_color:   .double 255.0, 128.0, 64.0

.text
.global ray_sphere_intersect

# Function: ray_sphere_intersect
# Input:
#   v1 = ray origin (3D vector)
#   v2 = ray direction (3D vector, normalized)
#   r5 = pointer to sphere object
# Output:
#   f1 = intersection distance (or -1.0 if no intersection)
# Destroys: v3, v4, f2-f10

ray_sphere_intersect:
    # Load sphere center (1 instruction vs 3 scalar loads)
    lv v3, 0(r5)              # v3 = sphere center {x, y, z}

    # Compute w = ray_origin - sphere_center (1 instruction vs 3 scalar subs)
    vsub v4, v1, v3           # v4 = w vector

    # Compute b = 2 * dot(ray_direction, w)
    # Using vector dot product (1 instruction vs 5 scalar ops)
    vdot f2, v2, v4           # f2 = dot(direction, w)
    lif f3, 2.0               # f3 = 2.0
    fmul f4, f2, f3           # f4 = b

    # Compute c = dot(w, w) - radius²
    # VSQR computes length squared in 1 instruction (vs 5 scalar)
    vsqr f5, v4               # f5 = ||w||²
    lf f6, 24(r5)             # f6 = radius² (load from object)
    fsub f7, f5, f6           # f7 = c

    # Compute discriminant = b² - 4c
    # Note: a = 1 because ray direction is normalized
    fmul f8, f4, f4           # f8 = b²
    lif f9, 4.0               # f9 = 4.0
    fmul f10, f9, f7          # f10 = 4c
    fsub f8, f8, f10          # f8 = discriminant

    # Check if discriminant < 0 (no intersection)
    lif f0, 0.0
    fblt f8, f0, no_hit       # if discriminant < 0, no intersection

    # Compute t = (-b - sqrt(discriminant)) / 2
    fsqrt f9, f8              # f9 = sqrt(discriminant)
    fneg f4, f4               # f4 = -b
    fsub f10, f4, f9          # f10 = -b - sqrt(d)
    lif f2, 0.5               # f2 = 0.5
    fmul f1, f10, f2          # f1 = t (final result)

    ret                       # Return with t in f1

no_hit:
    lif f1, -1.0              # Return -1.0 for no intersection
    ret

# Function: get_surface_normal
# Compute surface normal at intersection point
# Input:
#   v1 = intersection point
#   r5 = pointer to sphere object
# Output:
#   v2 = normalized surface normal
# Destroys: v3

get_surface_normal:
    # Load sphere center
    lv v3, 0(r5)              # v3 = center

    # Normal = normalize(point - center)
    vsub v2, v1, v3           # v2 = point - center
    vnorm v2, v2              # v2 = normalized normal (1 instruction!)

    ret

# Function: compute_lighting
# Compute diffuse lighting
# Input:
#   v1 = surface normal (normalized)
#   v2 = light direction (normalized)
#   f1 = diffuse coefficient
# Output:
#   f2 = lighting intensity [0, 1]

compute_lighting:
    # Compute dot product of normal and light direction
    vdot f2, v1, v2           # f2 = dot(normal, light)

    # Clamp to [0, 1]
    lif f0, 0.0
    fmax f2, f2, f0           # f2 = max(0, dot)

    # Scale by diffuse coefficient
    fmul f2, f2, f1           # f2 = intensity

    ret

# Function: trace_ray
# Main ray tracing function (simplified)
# Input:
#   v1 = ray origin
#   v2 = ray direction (normalized)
#   r3 = pointer to object array
#   r4 = number of objects
# Output:
#   v3 = RGB color

trace_ray:
    # Save return address and callee-saved registers
    addi r2, r2, -32          # Allocate stack frame
    sw r1, 0(r2)              # Save return address
    sv v5, 8(r2)              # Save callee-saved vector

    # Initialize minimum distance
    lif f10, 1000000.0        # f10 = tmin
    li r10, -1                # r10 = closest object index

    # Initialize loop counter
    li r6, 0                  # r6 = current object index

object_loop:
    # Check if we've processed all objects
    bge r6, r4, done_objects  # if i >= num_objects, exit loop

    # Get pointer to current object
    li r7, 128                # Size of object struct
    mul r8, r6, r7            # Offset = index * sizeof(object)
    add r9, r3, r8            # r9 = pointer to current object

    # Call intersection test
    # (In real implementation, would dispatch based on object type)
    jal r1, ray_sphere_intersect  # Returns t in f1

    # Check if this is closer than current minimum
    lif f0, 0.0
    fblt f1, f0, next_object  # if t < 0, skip
    fbge f1, f10, next_object # if t >= tmin, skip

    # Update minimum
    # (Use FMA for efficient min update)
    sf f1, 0(r2)              # Save new tmin
    sw r6, 8(r2)              # Save object index

next_object:
    addi r6, r6, 1            # i++
    jump object_loop

done_objects:
    # Check if we hit anything
    li r7, -1
    beq r10, r7, background   # if no hit, return background color

    # We hit something - compute shading
    # Load hit object
    # ... (shading computation)

    # Return color in v3
    lv v3, hit_color(r0)
    jump cleanup

background:
    # Return background color (black)
    lif f1, 0.0
    lif f2, 0.0
    lif f3, 0.0
    vset v3, f1, f2, f3       # v3 = {0, 0, 0}

cleanup:
    # Restore registers and return
    lw r1, 0(r2)              # Restore return address
    lv v5, 8(r2)              # Restore vector register
    addi r2, r2, 32           # Deallocate stack frame
    ret

# Function: render_pixel
# Render a single pixel
# Input:
#   r3 = x coordinate
#   r4 = y coordinate
#   r5 = width
#   r6 = height
# Output:
#   r7, r8, r9 = RGB bytes

render_pixel:
    # Convert pixel coordinates to screen space
    # screen_x = (x - width/2) * (128.0 / width)

    # Compute x - width/2 (using FMA for efficiency)
    # Convert to float
    # ... (coordinate transformation)

    # Build ray direction
    # ... (using vector operations)

    # Set ray origin to camera position
    lv v1, camera_pos(r0)     # Load camera position

    # Call trace_ray
    jal r1, trace_ray         # Returns color in v3

    # Convert float color to bytes
    vget f1, v3, 0            # f1 = red
    vget f2, v3, 1            # f2 = green
    vget f3, v3, 2            # f3 = blue

    # Clamp and convert to int
    # ... (clamping logic)

    ret

# Main rendering loop
main:
    # Initialize
    jal r1, read_scene_data

    # Setup rendering parameters
    li r3, 64                 # width
    li r4, 64                 # height

    # Nested loops for all pixels
    li r5, 0                  # y = 0
y_loop:
    bge r5, r4, done_render   # if y >= height, done

    li r6, 0                  # x = 0
x_loop:
    bge r6, r3, next_row      # if x >= width, next row

    # Render pixel at (x, y)
    # ... (render pixel logic)

    # Write pixel to output
    writeb r7                 # Write red
    writeb r8                 # Write green
    writeb r9                 # Write blue

    addi r6, r6, 1            # x++
    jump x_loop

next_row:
    addi r5, r5, 1            # y++
    jump y_loop

done_render:
    halt                      # Stop execution

# End of sample code
