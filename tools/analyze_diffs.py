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

def analyze_diff_distribution(file1, file2):
    _, _, _, data1 = read_ppm(file1)
    _, _, _, data2 = read_ppm(file2)

    if len(data1) != len(data2):
        print(f"ERROR: Data sizes differ")
        return

    # Histogram of differences
    diff_hist = {}
    large_diffs = []

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
            diff_hist[diff] = diff_hist.get(diff, 0) + 1

        if diff > 10:
            pixel_idx = i // 3
            x = pixel_idx % 64
            y = pixel_idx // 64
            large_diffs.append((pixel_idx, x, y, (r1, g1, b1), (r2, g2, b2), diff))

    print("Difference histogram:")
    for diff in sorted(diff_hist.keys()):
        print(f"  Diff {diff}: {diff_hist[diff]} pixels ({diff_hist[diff] * 100.0 / 4096:.2f}%)")

    print(f"\nLarge differences (>10):")
    print(f"Count: {len(large_diffs)}")
    if large_diffs:
        print("\nFirst 30 large differences:")
        for pixel_idx, x, y, (r1, g1, b1), (r2, g2, b2), diff in large_diffs[:30]:
            print(f"  Pixel ({x},{y}): ({r1},{g1},{b1}) vs ({r2},{g2},{b2}) - diff {diff}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <file1.ppm> <file2.ppm>")
        sys.exit(1)

    analyze_diff_distribution(sys.argv[1], sys.argv[2])
