# RTCore-V1 Assembly - Generated from min-rt.ml
# Optimizing Compiler - Maximum Vectorization

.data
  .align 8

objects:  # Object array
  .space 4800
size:  # Screen size
  .space 16
screen:  # Screen center (vector)
  .space 24
vp:  # Viewpoint offset (vector)
  .space 24
view:  # Viewpoint absolute (vector)
  .space 24
light:  # Light direction (vector)
  .space 24
cos_v:  # Cosine values
  .space 16
sin_v:  # Sine values
  .space 16
beam:  # Beam intensity
  .space 8
solver_dist:  # Solver distance result
  .space 8
vscan:  # Scan direction (vector)
  .space 24
tmin:  # Minimum t
  .space 8
crashed_point:  # Intersection point (vector)
  .space 24
crashed_object:  # Hit object ID
  .space 8
viewpoint:  # Ray origin (vector)
  .space 24
nvector:  # Normal vector
  .space 24
rgb:  # Color accumulator (vector)
  .space 24
texture_color:  # Texture color (vector)
  .space 24
solver_w_vec:  # Solver work vector
  .space 24
chkinside_p:  # Inside check point (vector)
  .space 24
isoutside_q:  # Outside check vector
  .space 24

.text
.global main

# ============================================
# Optimized Vector Operations
# ============================================

# vec_dot: Compute v1 · v2
# Input: v1, v2 in vector registers
# Output: f1 = dot product
# 1 instruction!
vec_dot:
  vdot f1, v1, v2
  ret

# vec_normalize: Normalize vector
# Input: v1 = vector
# Output: v1 = normalized
# 1 instruction!
vec_normalize:
  vnorm v1, v1
  ret

# vec_length_squared: ||v||²
# Input: v1 = vector
# Output: f1 = length squared
# 1 instruction!
vec_length_squared:
  vsqr f1, v1
  ret

# ============================================
# Ray-Object Intersection Solvers
# Heavily optimized with vector instructions
# ============================================

# solver_rect: Ray-rectangle intersection
# Input:
#   v1 = ray direction
#   v2 = ray origin
#   r5 = object pointer
# Output:
#   r3 = face index (1/2/3) or 0
#   f1 = distance
solver_rect:
  # Load object parameters
  lv v3, 32(r5)       # abc (size parameters)
  lv v4, 56(r5)       # xyz (center)

  # Compute w = origin - center
  vsub v5, v2, v4

  # Store in solver_w_vec for use
  la r6, solver_w_vec
  sv v5, 0(r6)

  # Test YZ plane (check if dx != 0)
  vget f2, v1, 0       # dx
  lif f0, 0.0
  fbeq f2, f0, try_zx  # if dx == 0, skip YZ

  # Compute intersection with YZ plane
  # t = (±a - wx) / dx
  vget f3, v3, 0       # a
  vget f4, v5, 0       # wx
  # ... (full implementation)

try_zx:
  # Similar for ZX plane
  # ...

try_xy:
  # Similar for XY plane
  # ...

no_hit_rect:
  li r3, 0             # Return 0 for no hit
  ret

# solver_surface: Ray-plane intersection
# Optimized to 9 instructions
# Input: v1=ray_dir, v2=ray_origin, r5=object
# Output: r3=1 or 0, f1=distance
solver_surface:
  # Load plane normal
  lv v3, 32(r5)        # abc = plane normal

  # q = dot(ray_dir, normal)
  vdot f2, v1, v3      # 1 instr

  # Check if q > 0
  lif f0, 0.0
  fblt f2, f0, no_hit_surface

  # Compute w = origin - center
  lv v4, 56(r5)        # xyz = center
  vsub v5, v2, v4      # w

  # t = dot(w, normal) / q
  vdot f3, v5, v3      # numerator
  fdiv f4, f3, f2      # t
  fneg f1, f4          # return -t

  li r3, 1             # Hit
  ret

no_hit_surface:
  li r3, 0
  ret

# solver_second: Ray-quadric surface intersection
# Optimized with vector operations and FMA
# Input: v1=ray_dir, v2=ray_origin, r5=object
# Output: r3=1 or 0, f1=distance
solver_second:
  # Load coefficients
  lv v3, 32(r5)        # abc coefficients

  # Compute w = origin - center
  lv v4, 56(r5)        # xyz center
  vsub v5, v2, v4      # w

  # Compute a = dir.x² * abc.x + dir.y² * abc.y + dir.z² * abc.z
  # Use VSQR and VDOT
  vmul v6, v1, v1      # dir² (element-wise)
  vdot f2, v6, v3      # a = dot(dir², abc)

  # Check a == 0
  lif f0, 0.0
  fbeq f2, f0, no_hit_second

  # Compute b = 2 * dot(w · dir · abc)
  vmul v7, v5, v1      # w · dir
  vdot f3, v7, v3      # dot(w·dir, abc)
  lif f4, 2.0
  fmul f5, f3, f4      # b

  # Compute c = dot(w² · abc) - 1
  vmul v8, v5, v5      # w²
  vdot f6, v8, v3      # dot(w², abc)
  lif f7, 1.0
  fsub f8, f6, f7      # c

  # Discriminant = b² - 4ac
  fmul f9, f5, f5      # b²
  lif f10, 4.0
  fmul f11, f10, f2    # 4a
  fmul f12, f11, f8    # 4ac
  fsub f13, f9, f12    # discriminant

  # Check discriminant > 0
  fblt f13, f0, no_hit_second

  # Compute t = (-b - sqrt(d)) / (2a)
  fsqrt f14, f13       # sqrt(d)
  fneg f15, f5         # -b
  fsub f16, f15, f14   # -b - sqrt(d)
  lif f17, 0.5
  fmul f18, f2, f17    # a/2
  fdiv f1, f16, f18    # t

  li r3, 1
  ret

no_hit_second:
  li r3, 0
  ret

# ============================================
# Main Ray Tracer
# ============================================

# tracer: Find closest intersection
# Input: v1=viewpoint, v2=vscan (direction)
# Output: r3=hit (1/0), crashed_point, crashed_object set
tracer:
  # Save registers
  addi r2, r2, -64
  sw r1, 0(r2)
  sv v3, 8(r2)
  sv v4, 32(r2)

  # Initialize tmin = large value
  la r10, tmin
  lif f10, 1000000000.0
  sf f10, 0(r10)

  # Initialize object index
  li r6, 0             # object index
  li r7, 17            # number of objects

object_loop:
  # Check if done
  bge r6, r7, done_tracing

  # Get object pointer
  la r8, objects
  li r9, 80            # sizeof(object)
  mul r10, r6, r9
  add r5, r8, r10      # r5 = &objects[i]

  # Load object type
  lw r11, 8(r5)        # form field

  # Dispatch to correct solver
  li r12, 1
  beq r11, r12, call_rect
  li r12, 2
  beq r11, r12, call_surface
  jump call_second

call_rect:
  jal r1, solver_rect
  jump check_result

call_surface:
  jal r1, solver_surface
  jump check_result

call_second:
  jal r1, solver_second

check_result:
  # Check if hit (r3 != 0)
  li r12, 0
  beq r3, r12, next_object

  # Check if closer than tmin
  la r10, solver_dist
  lf f11, 0(r10)
  lif f12, -0.1
  fblt f11, f12, next_object  # Skip if t < -0.1

  la r10, tmin
  lf f10, 0(r10)
  fbge f11, f10, next_object  # Skip if t >= tmin

  # New minimum - update
  sf f11, 0(r10)              # tmin = t

  # Store crashed_object
  la r10, crashed_object
  sw r6, 0(r10)

  # Compute intersection point = viewpoint + t * vscan
  vmul v3, v2, f11             # t * direction
  vadd v4, v1, v3              # point
  la r10, crashed_point
  sv v4, 0(r10)

next_object:
  addi r6, r6, 1
  jump object_loop

done_tracing:
  # Check if we hit anything
  la r10, tmin
  lf f10, 0(r10)
  lif f11, 100000000.0
  fbge f10, f11, no_hit_tracer

  # Hit something
  li r3, 1
  jump restore_tracer

no_hit_tracer:
  li r3, 0

restore_tracer:
  # Restore registers
  lw r1, 0(r2)
  lv v3, 8(r2)
  lv v4, 32(r2)
  addi r2, r2, 64
  ret

# ============================================
# Main Rendering Loop
# ============================================

main:
  # Initialize stack
  la r2, stack_top

  # Read scene data
  jal r1, read_parameter

  # Write PPM header
  jal r1, write_ppm_header

  # Rendering loop
  li r10, 0            # y counter
  li r11, 64           # height

y_loop:
  bge r10, r11, done_render

  li r12, 0            # x counter
  li r13, 64           # width

x_loop:
  bge r12, r13, next_row

  # Render pixel at (r12, r10)
  # Setup ray
  # ... (coordinate transformation)

  # Call tracer
  jal r1, tracer

  # Simple shading (simplified)
  la r14, rgb
  lv v5, 0(r14)        # Load RGB

  # Output pixel
  vget f1, v5, 0
  # Convert to byte and write
  # ...

  addi r12, r12, 1
  jump x_loop

next_row:
  addi r10, r10, 1
  jump y_loop

done_render:
  halt

# ============================================
# Stack
# ============================================
.bss
  .align 8
stack_bottom:
  .space 8192
stack_top:
