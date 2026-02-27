#!/usr/bin/env python3
"""
Extract all Group frameworks and variant components for the web explorer tool.
"""

import os
from PIL import Image

ROM_PATH = "../../Sangokushi (Japan).nes"

# NES palette for mob portraits
PALETTE = [
    (0, 0, 0),        # Index 0: Black
    (247, 216, 165),  # Index 1: Light skin
    (234, 158, 34),   # Index 2: Dark skin
    (255, 255, 255),  # Index 3: White
]

# 20 Groups with ROM addresses and tile counts
# 2026-02-27: 發現 0x1C014 有被使用 (T04)，重新編號所有 Groups
GROUPS = [
    (0x1C014, 24),  # G00 - 新發現! 使用 T00
    (0x1C194, 24),  # G01 (舊 G00)
    (0x1C314, 24),  # G02 (舊 G01)
    (0x1C494, 24),  # G03 (舊 G02)
    (0x1C614, 24),  # G04 (舊 G03) - 使用 T04!
    (0x1C794, 22),  # G05 (舊 G04)
    (0x1C914, 21),  # G06 (舊 G05)
    (0x1CA94, 20),  # G07 (舊 G06)
    (0x1CC14, 20),  # G08 (舊 G07)
    (0x1CD94, 21),  # G09 (舊 G08)
    (0x1CF14, 24),  # G10 (舊 G09)
    (0x1D094, 21),  # G11 (舊 G10)
    (0x1D214, 21),  # G12 (舊 G11)
    (0x1D394, 22),  # G13 (舊 G12)
    (0x1D514, 22),  # G14 (舊 G13)
    (0x1D694, 24),  # G15 (舊 G14)
    (0x1D814, 24),  # G16 (舊 G15)
    (0x1D994, 24),  # G17 (舊 G16)
    (0x1DB14, 24),  # G18 (舊 G17)
    (0x1DC94, 24),  # G19 (舊 G18)
]

# Group to Template mapping (現在是 1:1 對應)
GROUP_TO_TEMPLATE = {i: i for i in range(20)}

# Variant data locations
EYES_START = 0x1DE14    # 20 variants × 3 tiles × 16 bytes
FACES_START = 0x1E1D4   # 20 variants × 3 tiles × 16 bytes
MOUTHS_START = 0x1E594  # 20 variants × 6 tiles × 16 bytes

TEMPLATE_START = 0x1ED14  # 20 templates × 36 bytes


def decode_tile(data):
    """Decode 16 bytes of NES tile data to 8x8 pixel array."""
    pixels = []
    for y in range(8):
        plane0 = data[y]
        plane1 = data[y + 8]
        row = []
        for x in range(7, -1, -1):
            bit0 = (plane0 >> x) & 1
            bit1 = (plane1 >> x) & 1
            color_idx = bit0 + (bit1 << 1)
            row.append(color_idx)
        pixels.append(row)
    return pixels


def tile_to_image(tile_data, scale=1):
    """Convert tile pixel data to PIL Image."""
    img = Image.new('RGB', (8 * scale, 8 * scale))
    for y, row in enumerate(tile_data):
        for x, color_idx in enumerate(row):
            color = PALETTE[color_idx]
            for sy in range(scale):
                for sx in range(scale):
                    img.putpixel((x * scale + sx, y * scale + sy), color)
    return img


def read_template(rom_data, template_idx):
    """Read a 36-byte template and return as 6x6 grid."""
    offset = TEMPLATE_START + template_idx * 36
    template = rom_data[offset:offset + 36]
    grid = []
    for row in range(6):
        row_data = []
        for col in range(6):
            val = template[row * 6 + col]
            if val == 0:
                row_data.append(None)  # Variant position
            else:
                row_data.append(val - 0x64)  # Fixed tile index
        grid.append(row_data)
    return grid


def extract_group_framework(rom_data, group_idx, output_dir, scale=3):
    """Extract a group's framework tiles (without variants) as individual tile images."""
    base_addr, tile_count = GROUPS[group_idx]
    template_idx = GROUP_TO_TEMPLATE[group_idx]
    template = read_template(rom_data, template_idx)

    # Extract each tile
    group_dir = os.path.join(output_dir, f"group_{group_idx:02d}")
    os.makedirs(group_dir, exist_ok=True)

    for tile_idx in range(tile_count):
        tile_offset = base_addr + tile_idx * 16
        tile_data = decode_tile(rom_data[tile_offset:tile_offset + 16])
        img = tile_to_image(tile_data, scale)
        img.save(os.path.join(group_dir, f"tile_{tile_idx:02d}.png"))

    # Create framework image (48x48 at scale)
    framework_img = Image.new('RGB', (48 * scale, 48 * scale), (64, 64, 64))

    for row in range(6):
        for col in range(6):
            tile_idx = template[row][col]
            if tile_idx is not None and tile_idx < tile_count:
                tile_offset = base_addr + tile_idx * 16
                tile_data = decode_tile(rom_data[tile_offset:tile_offset + 16])
                tile_img = tile_to_image(tile_data, scale)
                framework_img.paste(tile_img, (col * 8 * scale, row * 8 * scale))

    framework_img.save(os.path.join(output_dir, f"framework_{group_idx:02d}.png"))

    # Also save the template info
    return template


def extract_variants(rom_data, output_dir, scale=3):
    """Extract all variant components (eyes, faces, mouths)."""
    variants_dir = os.path.join(output_dir, "variants")
    os.makedirs(variants_dir, exist_ok=True)

    # Eyes: 20 variants × 3 tiles
    eyes_dir = os.path.join(variants_dir, "eyes")
    os.makedirs(eyes_dir, exist_ok=True)
    for var_idx in range(20):
        var_img = Image.new('RGB', (24 * scale, 8 * scale), (0, 0, 0))
        for tile_idx in range(3):
            offset = EYES_START + (var_idx * 3 + tile_idx) * 16
            tile_data = decode_tile(rom_data[offset:offset + 16])
            tile_img = tile_to_image(tile_data, scale)
            var_img.paste(tile_img, (tile_idx * 8 * scale, 0))
        var_img.save(os.path.join(eyes_dir, f"eyes_{var_idx:02d}.png"))

    # Faces: 20 variants × 3 tiles
    faces_dir = os.path.join(variants_dir, "faces")
    os.makedirs(faces_dir, exist_ok=True)
    for var_idx in range(20):
        var_img = Image.new('RGB', (24 * scale, 8 * scale), (0, 0, 0))
        for tile_idx in range(3):
            offset = FACES_START + (var_idx * 3 + tile_idx) * 16
            tile_data = decode_tile(rom_data[offset:offset + 16])
            tile_img = tile_to_image(tile_data, scale)
            var_img.paste(tile_img, (tile_idx * 8 * scale, 0))
        var_img.save(os.path.join(faces_dir, f"faces_{var_idx:02d}.png"))

    # Mouths: 20 variants × 6 tiles (2 rows of 3)
    mouths_dir = os.path.join(variants_dir, "mouths")
    os.makedirs(mouths_dir, exist_ok=True)
    for var_idx in range(20):
        var_img = Image.new('RGB', (24 * scale, 16 * scale), (0, 0, 0))
        # Mouth tile layout: [0,1,4], [2,3,5] -> positions in 2x3 grid
        # ROM order: 0,1,2,3,4,5 = C1R4, C2R4, C1R5, C2R5, C3R4, C3R5
        layout = [(0, 0), (1, 0), (0, 1), (1, 1), (2, 0), (2, 1)]
        for tile_idx in range(6):
            offset = MOUTHS_START + (var_idx * 6 + tile_idx) * 16
            tile_data = decode_tile(rom_data[offset:offset + 16])
            tile_img = tile_to_image(tile_data, scale)
            col, row = layout[tile_idx]
            var_img.paste(tile_img, (col * 8 * scale, row * 8 * scale))
        var_img.save(os.path.join(mouths_dir, f"mouths_{var_idx:02d}.png"))


def generate_template_json(rom_data):
    """Generate JSON data for all templates."""
    templates = {}
    for g_idx in range(20):
        t_idx = GROUP_TO_TEMPLATE[g_idx]
        template = read_template(rom_data, t_idx)
        templates[g_idx] = {
            "template_idx": t_idx,
            "grid": template,
            "base_addr": hex(GROUPS[g_idx][0]),
            "tile_count": GROUPS[g_idx][1],
        }
    return templates


def main():
    output_dir = "assets"
    os.makedirs(output_dir, exist_ok=True)

    # Read ROM
    with open(ROM_PATH, "rb") as f:
        rom_data = f.read()

    print("Extracting Group frameworks...")
    templates_info = {}
    for g_idx in range(20):
        print(f"  Group {g_idx:02d}...")
        template = extract_group_framework(rom_data, g_idx, output_dir)
        templates_info[g_idx] = {
            "template_idx": GROUP_TO_TEMPLATE[g_idx],
            "grid": template,
            "base_addr": hex(GROUPS[g_idx][0]),
            "tile_count": GROUPS[g_idx][1],
        }

    print("Extracting variants (eyes, faces, mouths)...")
    extract_variants(rom_data, output_dir)

    # Generate JavaScript data file
    print("Generating JavaScript data file...")
    with open(os.path.join(output_dir, "data.js"), "w") as f:
        f.write("// Auto-generated data for variant explorer\n\n")
        f.write("const GROUPS = [\n")
        for g_idx in range(20):
            info = templates_info[g_idx]
            grid_str = str(info["grid"]).replace("None", "null")
            f.write(f"  {{ idx: {g_idx}, template: {info['template_idx']}, ")
            f.write(f"baseAddr: \"{info['base_addr']}\", tileCount: {info['tile_count']}, ")
            f.write(f"grid: {grid_str} }},\n")
        f.write("];\n\n")

        f.write("const VARIANT_COUNTS = { eyes: 20, faces: 20, mouths: 20 };\n")

    print("Done! Assets generated in:", output_dir)


if __name__ == "__main__":
    main()
