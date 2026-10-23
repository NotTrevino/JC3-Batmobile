#!/usr/bin/env python3

import struct
import sys
import os

# Path to the .toc file
file_path = r'E:\Modding\JC3-Batmobile\Builds\test-025\v0300_car_kensington_sportsmuscle_civilian_01.ee.toc'

# Open the .toc file in binary mode
with open(file_path, 'rb') as f:
    toc_data = f.read()

# Find the entry for 'sportsmuscle_vehicle_parts.vmodc'
offset_index = 0
name_len = 0
name = b''
while offset_index < len(toc_data):
    # Read name length
    name_len = struct.unpack_from('<I', toc_data, offset_index)[0]
    offset_index += 4
    # Read name
    name = toc_data[offset_index:offset_index + name_len]
    offset_index += name_len
    # Check if this is the target name
    if name.decode('utf-8') == 'sportsmuscle_vehicle_parts.vmodc':
        # Read offset and size
        current_offset, current_size = struct.unpack_from('<II', toc_data, offset_index)
        offset_index += 8
        # Update the offset to 12158556
        new_offset = 12158556
        toc_data = toc_data[:offset_index - 8] + struct.pack('<II', new_offset, current_size) + toc_data[offset_index:]
        print(f"Updated offset for {name.decode('utf-8')} to {new_offset}")
        break
    else:
        # Skip to next entry
        offset_index += 8

# Write the updated .toc file
with open(file_path, 'wb') as f:
    f.write(toc_data)

print(f"Updated .toc file at {file_path}")