#!/usr/bin/env python3
"""
Debug a specific pixel to see why it's not rendering correctly
"""
import sys
sys.path.insert(0, '.')
import minrt_correct
import math

def parse_sld_file(filename):
    data = []
    with open(filename) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            tokens = line.split()
            for token in tokens:
                try:
                    if '.' in token:
                        data.append(float(token))
                    else:
                        data.append(int(token))
                except ValueError:
                    pass
    return data

# Load scene
scene_data = parse_sld_file('contest.sld')
rt = minrt_correct.MinRT()
rt.read_parameter(scene_data)

# Set up for rendering
width, height = 64, 64
rt.setup_screen(width, height)

# Debug pixel (11, 10) which should be (124,139,22) but we get (31,0,0)
x, y = 11, 10

# Calculate scan direction for this pixel
print(f"Debugging pixel ({x},{y})")
print(f"Expected: (124,139,22)")
print(f"Screen size: {width}x{height}")
print(f"Viewpoint: {rt.viewpoint}")
print(f"View direction: {rt.view}")
print(f"Up vector (before scan): {rt.vscan}")

# This is from the scan_point function
xn = (x - width / 2) / (width / 2)
yn = -(y - height / 2) / (height / 2)

rt.vscan[0] = rt.cos_v[0] * (xn * rt.view[1] + yn * rt.cos_v[1] * rt.view[0]) + rt.sin_v[0] * (yn * rt.sin_v[1])
rt.vscan[1] = xn * (-rt.view[0]) + yn * rt.cos_v[1] * rt.view[1]
rt.vscan[2] = rt.sin_v[0] * (xn * rt.view[1] + yn * rt.cos_v[1] * rt.view[0]) - rt.cos_v[0] * (yn * rt.sin_v[1])

print(f"Scan direction for pixel: {rt.vscan}")

# Now trace
rt.rgb = [0.0, 0.0, 0.0]
rt.tmin[0] = 1000000000.0

print(f"\nTracing...")
print(f"or_net[0] has {len(rt.or_net[0])} entries")
for i, entry in enumerate(rt.or_net[0]):
    print(f"  Entry {i}: {entry}")

crashed = rt.tracer(rt.viewpoint, rt.vscan)
print(f"\nTracer result: crashed={crashed}")
print(f"tmin: {rt.tmin[0]}")
if crashed:
    print(f"Crashed object: {rt.crashed_object[0]}")
    print(f"Crashed point: {rt.crashed_point}")

print(f"\nFinal RGB before raytracing: {rt.rgb}")

# Now do raytracing
rt.raytracing(0, 1.0)

print(f"Final RGB after raytracing: {rt.rgb}")
red = int(rt.rgb[0])
green = int(rt.rgb[1])
blue = int(rt.rgb[2])
red = min(255, max(0, red))
green = min(255, max(0, green))
blue = min(255, max(0, blue))
print(f"Final pixel color: ({red},{green},{blue})")
