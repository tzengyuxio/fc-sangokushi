#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FC 三國志 頭像匯出工具

根據逆向工程分析結果，從 ROM 匯出 48×48 頭像圖形。
"""

import os
import sys

try:
    from PIL import Image
except ImportError:
    print("需要安裝 Pillow: pip3 install Pillow")
    sys.exit(1)

# ─── 常數 ────────────────────────────────────────────────────

# 頭像指標表
PORTRAIT_PTR_TABLE = 0x1BC38
PORTRAIT_COUNT = 81

# 武將→頭像映射
# 頭像索引存於姓名表 (0x3A314) 每筆記錄的 byte 14
# 公式: portrait_index = 姓名表[char_idx * 15 + 14] - 1
NAME_TABLE = 0x3A314
NAME_RECORD_SIZE = 15
CHARACTER_COUNT = 256

# 排列表
ARRANGEMENT_TABLE = 0x1B140
ARRANGEMENT_COUNT = 78  # 排列表中的條目數 (原認為 60，實際延伸到頭像指標表)

# 色盤 (從遊戲截圖校準)
PALETTE = [
    (0, 0, 0),          # 0: 黑
    (247, 216, 165),    # 1: 淺膚色
    (234, 158, 34),     # 2: 深膚色
    (255, 255, 255),    # 3: 白
]

# 標準 2×2 metatile 排列 (36-tile 頭像用)
STANDARD_LAYOUT = [
    [ 1,  2,  5,  6,  9, 10],
    [ 3,  4,  7,  8, 11, 12],
    [13, 14, 17, 18, 21, 22],
    [15, 16, 19, 20, 23, 24],
    [25, 26, 29, 30, 33, 34],
    [27, 28, 31, 32, 35, 36],
]

# 36-tile 頭像索引 (32 個)
STANDARD_36_PORTRAITS = {6, 7, 8, 24, 25, 26, 29, 35, 38, 40, 41, 43, 44, 45, 46, 47, 49, 51, 58, 59,
                         61, 66, 68, 69, 70, 72, 74, 75, 76, 77, 79, 80}

# P01 的自訂排列 (不在排列表中，手動校正)
PORTRAIT_01_LAYOUT = [
    [ 1,  2,  5,  6,  9, 10],
    [ 3,  4,  7,  8, 11, 12],
    [10, 13, 15, 16, 19, 20],
    [10, 14, 17, 18, 21, 22],
    [10, 23, 26, 27, 30, 10],
    [24, 25, 28, 29, 31, 32],
]

# 手動校正的頭像→排列索引映射 (通過視覺比對確認)
# 格式: portrait_index: arrangement_index
MANUAL_PORTRAIT_MAPPING = {
    # tile_count=32 組
    # 1: 使用 PORTRAIT_01_LAYOUT (自訂排列)
    5: 27,   # 孫權, A2/A17/A18/A27 都可以
    20: 2,   # A2, A17, A18, A27 都可以
    21: 17,  # A2, A17, A18, A27 都可以
    30: 18,  # A2, A17, A18, A27 都可以
    31: 28,
    33: 30,
    36: 33,
    54: 51,
    # tile_count=33 組
    2: 12,
    11: 8,
    15: 12,
    16: 13,
    17: 14,
    18: 14,  # A14, A15 都可以，選 A14
    34: 31,
    39: 36,
    48: 45,
    56: 31,
    64: 31,
    # tile_count=35 組
    63: 60,
    65: 62,  # A62, A68 都可以，選 A62
    67: 57,  # A57, A64 都可以，選 A57
    71: 62,  # A62, A68 都可以，選 A62
    73: 70,
    78: 75,
}


def load_rom(path):
    with open(path, 'rb') as f:
        return f.read()


def read_portrait_ptr_table(rom):
    """讀取頭像指標表"""
    portraits = []
    for i in range(PORTRAIT_COUNT):
        offset = PORTRAIT_PTR_TABLE + i * 4
        bank = rom[offset]
        tile_count = rom[offset + 1]
        addr_lo = rom[offset + 2]
        addr_hi = rom[offset + 3]
        addr = addr_lo | (addr_hi << 8)
        file_offset = bank * 0x4000 + (addr - 0x8000) + 0x10
        portraits.append({
            'index': i,
            'bank': bank,
            'tile_count': tile_count,
            'addr': addr,
            'file_offset': file_offset,
            'is_standard': i in STANDARD_36_PORTRAITS
        })
    return portraits


def load_all_arrangements(rom):
    """載入所有排列資料"""
    arrangements = []
    for arr_idx in range(ARRANGEMENT_COUNT):
        offset = ARRANGEMENT_TABLE + arr_idx * 36
        data = rom[offset:offset + 36]
        rom_tiles = [b - 0x63 if 0x64 <= b <= 0x87 else b for b in data]
        layout = [rom_tiles[row * 6:(row + 1) * 6] for row in range(6)]
        max_tile = max(t for t in rom_tiles if 1 <= t <= 36) if any(1 <= t <= 36 for t in rom_tiles) else 0
        arrangements.append({
            'index': arr_idx,
            'layout': layout,
            'max_tile': max_tile,
            'is_standard': layout == STANDARD_LAYOUT
        })
    return arrangements


def find_arrangement_for_portrait(portrait, arrangements):
    """為頭像找到合適的排列"""
    tile_count = portrait['tile_count']

    # 36-tile 頭像使用標準排列
    if tile_count == 36:
        return STANDARD_LAYOUT

    # 找 max_tile == tile_count 的排列 (最佳匹配)
    for arr in arrangements:
        if arr['max_tile'] == tile_count and not arr['is_standard']:
            return arr['layout']

    # 找 max_tile < tile_count 的排列 (可接受)
    for arr in arrangements:
        if arr['max_tile'] < tile_count and not arr['is_standard']:
            return arr['layout']

    # 找不到，使用標準排列
    return STANDARD_LAYOUT


def decode_tile(rom, offset):
    """解碼 NES 8×8 tile"""
    if offset + 16 > len(rom):
        return [[0] * 8 for _ in range(8)]

    pixels = []
    for y in range(8):
        plane0 = rom[offset + y]
        plane1 = rom[offset + y + 8]
        row = []
        for x in range(7, -1, -1):
            bit0 = (plane0 >> x) & 1
            bit1 = (plane1 >> x) & 1
            row.append(bit0 | (bit1 << 1))
        pixels.append(row)
    return pixels


def generate_portrait(rom, portrait, layout):
    """生成頭像圖像"""
    file_offset = portrait['file_offset']
    tile_count = portrait['tile_count']

    # 讀取 tiles
    tiles = []
    for i in range(tile_count):
        tile_offset = file_offset + i * 16
        tile_pixels = decode_tile(rom, tile_offset)
        tiles.append(tile_pixels)

    # 建立 48×48 圖像
    img = Image.new('RGB', (48, 48), PALETTE[0])

    # 繪製
    for display_y in range(6):
        for display_x in range(6):
            rom_tile_num = layout[display_y][display_x]
            if rom_tile_num <= 0 or rom_tile_num > tile_count:
                continue
            tile_pixels = tiles[rom_tile_num - 1]
            for y in range(8):
                for x in range(8):
                    px = display_x * 8 + x
                    py = display_y * 8 + y
                    img.putpixel((px, py), PALETTE[tile_pixels[y][x]])

    return img


def build_portrait_arrangement_mapping(portraits, arrangements):
    """建立頭像到排列的映射（優先使用手動映射，其餘貪婪匹配）"""
    mapping = {}
    used_arrangements = set()

    # 建立排列索引到 layout 的查找表
    arr_by_index = {arr['index']: arr for arr in arrangements}

    # 先處理手動映射
    for portrait_idx, arr_idx in MANUAL_PORTRAIT_MAPPING.items():
        if arr_idx in arr_by_index:
            mapping[portrait_idx] = arr_by_index[arr_idx]['layout']
            used_arrangements.add(arr_idx)

    # 處理剩餘的非標準頭像
    non_standard_portraits = [p for p in portraits if not p['is_standard'] and p['index'] not in mapping]

    # 按 tile_count 排序，優先處理 tile 數較少的（更容易找到唯一匹配）
    non_standard_portraits.sort(key=lambda p: p['tile_count'])

    for p in non_standard_portraits:
        tile_count = p['tile_count']
        best_arr = None

        # 找 max_tile == tile_count 且未被使用的排列
        for arr in arrangements:
            if arr['index'] not in used_arrangements and not arr['is_standard']:
                if arr['max_tile'] == tile_count:
                    best_arr = arr
                    break

        # 如果沒找到，找 max_tile < tile_count 且未被使用的
        if best_arr is None:
            for arr in arrangements:
                if arr['index'] not in used_arrangements and not arr['is_standard']:
                    if arr['max_tile'] < tile_count:
                        best_arr = arr
                        break

        if best_arr:
            mapping[p['index']] = best_arr['layout']
            used_arrangements.add(best_arr['index'])
        else:
            # 使用標準排列作為 fallback
            mapping[p['index']] = STANDARD_LAYOUT

    return mapping


def export_all_portraits(rom, output_dir, scale=2):
    """匯出所有頭像"""
    os.makedirs(output_dir, exist_ok=True)

    portraits = read_portrait_ptr_table(rom)
    arrangements = load_all_arrangements(rom)
    mapping = build_portrait_arrangement_mapping(portraits, arrangements)

    print(f"匯出 {PORTRAIT_COUNT} 個頭像到 {output_dir}/")
    print(f"  36-tile 頭像: {len(STANDARD_36_PORTRAITS)} 個")
    print(f"  <36-tile 頭像: {PORTRAIT_COUNT - len(STANDARD_36_PORTRAITS)} 個")
    print()

    for p in portraits:
        if p['index'] == 1:
            layout = PORTRAIT_01_LAYOUT  # P01 使用自訂排列
        elif p['is_standard']:
            layout = STANDARD_LAYOUT
        else:
            layout = mapping.get(p['index'], STANDARD_LAYOUT)

        img = generate_portrait(rom, p, layout)

        if scale > 1:
            img = img.resize((48 * scale, 48 * scale), Image.NEAREST)

        output_path = os.path.join(output_dir, f"portrait_{p['index']:02d}.png")
        img.save(output_path)

    print(f"完成! 已儲存 {PORTRAIT_COUNT} 個頭像")


def export_portrait_atlas(rom, output_path, scale=2):
    """匯出頭像總覽圖"""
    portraits = read_portrait_ptr_table(rom)
    arrangements = load_all_arrangements(rom)
    mapping = build_portrait_arrangement_mapping(portraits, arrangements)

    cols = 9
    rows = 9
    size = 48 * scale
    margin = 2

    img_width = cols * (size + margin) + margin
    img_height = rows * (size + margin) + margin

    atlas = Image.new('RGB', (img_width, img_height), (128, 128, 128))

    for i, p in enumerate(portraits):
        if p['index'] == 1:
            layout = PORTRAIT_01_LAYOUT  # P01 使用自訂排列
        elif p['is_standard']:
            layout = STANDARD_LAYOUT
        else:
            layout = mapping.get(p['index'], STANDARD_LAYOUT)

        portrait_img = generate_portrait(rom, p, layout)
        if scale > 1:
            portrait_img = portrait_img.resize((size, size), Image.NEAREST)

        row = i // cols
        col = i % cols
        x = margin + col * (size + margin)
        y = margin + row * (size + margin)
        atlas.paste(portrait_img, (x, y))

    atlas.save(output_path)
    print(f"已儲存頭像總覽: {output_path}")


def main():
    rom_path = sys.argv[1] if len(sys.argv) > 1 else "Sangokushi (Japan).nes"

    if not os.path.exists(rom_path):
        print(f"錯誤: 找不到 ROM 檔案 '{rom_path}'")
        sys.exit(1)

    rom = load_rom(rom_path)

    if rom[:4] != b"NES\x1a":
        print("錯誤: 非有效的 iNES ROM 檔案")
        sys.exit(1)

    print(f"載入 ROM: {rom_path}")
    print(f"檔案大小: {len(rom)} bytes")
    print()

    output_dir = "kanji_output/portraits"
    export_all_portraits(rom, output_dir, scale=2)
    print()

    atlas_path = "kanji_output/portrait_atlas.png"
    export_portrait_atlas(rom, atlas_path, scale=2)


if __name__ == "__main__":
    main()
