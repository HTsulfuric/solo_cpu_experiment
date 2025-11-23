#!/usr/bin/env python3
import sys

def read_ppm(filename):
    with open(filename, 'rb') as f:
        # Read header
        magic = f.readline().strip()
        dims = f.readline().strip()
        maxval = f.readline().strip()

        # Read binary data
        data = f.read()

    return magic, dims, maxval, data

def compare_ppm(file1, file2):
    magic1, dims1, maxval1, data1 = read_ppm(file1)
    magic2, dims2, maxval2, data2 = read_ppm(file2)

    print(f"File 1: {file1}")
    print(f"  Magic: {magic1}, Dims: {dims1}, MaxVal: {maxval1}, Data size: {len(data1)}")
    print(f"File 2: {file2}")
    print(f"  Magic: {magic2}, Dims: {dims2}, MaxVal: {maxval2}, Data size: {len(data2)}")
    print()

    if len(data1) != len(data2):
        print(f"ERROR: Data sizes differ: {len(data1)} vs {len(data2)}")
        return

    # Compare pixel by pixel
    diffs = []
    total_diff = 0
    max_diff = 0

    for i in range(0, len(data1), 3):
        if i + 2 >= len(data1):
            break

        r1, g1, b1 = data1[i], data1[i+1], data1[i+2]
        r2, g2, b2 = data2[i], data2[i+1], data2[i+2]

        diff_r = abs(r1 - r2)
        diff_g = abs(g1 - g2)
        diff_b = abs(b1 - b2)
        diff = max(diff_r, diff_g, diff_b)

        if diff > 0:
            pixel_idx = i // 3
            diffs.append((pixel_idx, (r1, g1, b1), (r2, g2, b2), diff))
            total_diff += diff
            max_diff = max(max_diff, diff)

    print(f"Total pixels: {len(data1) // 3}")
    print(f"Different pixels: {len(diffs)}")
    print(f"Percentage different: {len(diffs) * 100.0 / (len(data1) // 3):.2f}%")
    print(f"Max difference: {max_diff}")
    print(f"Average difference (of different pixels): {total_diff / len(diffs) if diffs else 0:.2f}")
    print()

    if len(diffs) > 0:
        print("First 20 differences:")
        for i, (pixel_idx, (r1, g1, b1), (r2, g2, b2), diff) in enumerate(diffs[:20]):
            print(f"  Pixel {pixel_idx}: ({r1},{g1},{b1}) vs ({r2},{g2},{b2}) - diff {diff}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <file1.ppm> <file2.ppm>")
        sys.exit(1)

    compare_ppm(sys.argv[1], sys.argv[2])
