#!/usr/bin/env python3

import struct

# Paths to the .ee file and desired .toc file
nee_path = r'E:\Modding\JC3-Batmobile\Builds\test-024\v0300_car_kensington_sportsmuscle_civilian_01.ee'  # Using test-024's .ee to ensure correct structure

toc_path = r'E:\Modding\JC3-Batmobile\Builds\test-025\v0300_car_kensington_sportsmuscle_civilian_01.ee.toc'

# Define the entries for the .toc file
entries = {
    'sportsmuscle_vehicle_parts.vmodc': (12158556, 29886),  # Offset and size for the modified file
    'v0300_car_kensington_sportsmuscle_civilian_01.epe': (0, 109526),  # Example: vanilla .epe
    'v0300_car_kensington_sportsmuscle_civilian_01.stringlookup': (0, 2210),  # Example: vanilla stringlookup
    'editor/entities/jc_cameras/vehicle_cameras/car_base.ctunec': (0, 12260920),  # Example: vanilla car_base.ctunec
    # Add other entries as needed, using the same offset/size as test-024's .toc
}

# Generate the .toc file
with open(toc_path, 'wb') as toc_file:
    for name, (offset, size) in entries.items():
        # Write the name (null-terminated)
        name_bytes = name.encode('utf-8') + b'\0'  # Null-terminated
        toc_file.write(struct.pack('<I', len(name_bytes)))  # Name length
        toc_file.write(name_bytes)
        # Write the offset and size
        toc_file.write(struct.pack('<II', offset, size))

print(f"Generated .toc file at {toc_path}")