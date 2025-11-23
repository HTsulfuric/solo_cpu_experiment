#!/usr/bin/env python3
"""
Convert PPM to PNG
"""

import struct
import sys


def ppm_to_png(ppm_file, png_file):
    """Convert PPM P6 format to PNG"""
    # Read PPM
    with open(ppm_file, 'rb') as f:
        # Read header
        magic = f.readline().strip()
        if magic != b'P6':
            raise ValueError(f"Not a P6 PPM file: {magic}")

        # Skip comments
        line = f.readline()
        while line.startswith(b'#'):
            line = f.readline()

        # Read dimensions
        width, height = map(int, line.split())

        # Read max value
        maxval = int(f.readline())

        # Read pixel data
        pixels = f.read()

    # Use PIL/Pillow to write PNG
    try:
        from PIL import Image
        import numpy as np

        # Convert to numpy array
        img_array = np.frombuffer(pixels, dtype=np.uint8).reshape(height, width, 3)

        # Create and save image
        img = Image.fromarray(img_array, 'RGB')
        img.save(png_file, 'PNG')

        print(f"Converted {ppm_file} to {png_file}")
        print(f"Image size: {width}x{height}")
        return True

    except ImportError:
        print("PIL/Pillow not available, trying manual PNG creation...")
        return write_png_manually(pixels, width, height, png_file)


def write_png_manually(pixels, width, height, png_file):
    """Write PNG manually without PIL"""
    import zlib

    # PNG signature
    png_signature = b'\x89PNG\r\n\x1a\n'

    # IHDR chunk
    ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    ihdr_chunk = make_chunk(b'IHDR', ihdr_data)

    # IDAT chunk - image data
    # Convert RGB to PNG scanlines (add filter byte to each row)
    scanlines = b''
    for y in range(height):
        scanlines += b'\x00'  # No filter
        scanlines += pixels[y * width * 3:(y + 1) * width * 3]

    compressed = zlib.compress(scanlines, 9)
    idat_chunk = make_chunk(b'IDAT', compressed)

    # IEND chunk
    iend_chunk = make_chunk(b'IEND', b'')

    # Write PNG file
    with open(png_file, 'wb') as f:
        f.write(png_signature)
        f.write(ihdr_chunk)
        f.write(idat_chunk)
        f.write(iend_chunk)

    print(f"Converted to {png_file} (manual PNG)")
    print(f"Image size: {width}x{height}")
    return True


def make_chunk(chunk_type, data):
    """Create a PNG chunk"""
    import zlib
    length = struct.pack('>I', len(data))
    crc = struct.pack('>I', zlib.crc32(chunk_type + data) & 0xffffffff)
    return length + chunk_type + data + crc


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: ppm_to_png.py <input.ppm> <output.png>")
        sys.exit(1)

    ppm_to_png(sys.argv[1], sys.argv[2])
