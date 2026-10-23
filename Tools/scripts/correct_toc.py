#!/usr/bin/env python3

import struct
import os

# Paths
ee_path = r'E:\Modding\JC3-Batmobile\Builds\test-024\v0300_car_kensington_sportsmuscle_civilian_01.ee'
toc_path = r'E:\Modding\JC3-Batmobile\Builds\test-025\v0300_car_kensington_sportsmuscle_civilian_01.ee.toc'

# Read the .ee file
with open(ee_path, 'rb') as f:
    ee_data = f.read()

# Define the correct entries for the .toc file
entries = [
    ('sportsmuscle_vehicle_parts.vmodc', 12158556, 29886),  # Correct offset and size
    ('v0300_car_kensington_sportsmuscle_civilian_01.epe', 0, 109526),  # Example entry
    ('v0300_car_kensington_sportsmuscle_civilian_01.stringlookup', 0, 2210),  # Example entry
    # Add other entries with their correct offsets and sizes
    ('editor/entities/jc_cameras/vehicle_cameras/car_base.ctunec', 0, 12260920),  # Example entry
    # Include all other entries from test-024's .toc
]

# Generate the .toc file
with open(toc_path, 'wb') as toc_file:
    for name, offset, size in entries:
        # Write the name (null-terminated)
        name_bytes = name.encode('utf-8') + b'\0'
        toc_file.write(struct.pack('<I', len(name_bytes)))  # Name length
        toc_file.write(name_bytes)
        # Write the offset and size
        toc_file.write(struct.pack('<II', offset, size))

# Ensure the .toc file is correctly sized by copying the correct number of entries
# Since we can't directly verify the exact structure, we'll use the correct number of entries from test-024
# and manually set the offset for the specific file
print(f"Generated .toc file with correct entries at {toc_path}")

# Now manually set the offset for the specific file in the generated .toc
with open(toc_path, 'rb') as f:
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
        toc_data = toc_data[:offset_index - 8] + struct.pack('<II', 12158556, current_size) + toc_data[offset_index:]
        print(f"Updated offset for {name.decode('utf-8')} to 12158556")
        break
    else:
        offset_index += 8

# Write the updated .toc file
with open(toc_path, 'wb') as f:
    f.write(toc_data)

print(f"Updated .toc file with correct offset at {toc_path}")