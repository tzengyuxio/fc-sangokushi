# 大眾臉頭像系統 Pseudo Code

本文件說明大眾臉頭像系統 (portrait_id 81-254) 的結構與繪製流程。

> **注意**: 此系統的部分機制尚未完全解明，標記為 `[待確認]` 的部分需要進一步逆向工程。

## 系統概要

| 項目 | 標準頭像系統 | 大眾臉頭像系統 |
|------|--------------|----------------|
| 索引範圍 | 0-80 (81 個) | 81-254 (174 個) |
| 結構 | 完整獨立頭像 | 共用框架 + 可替換組件 |
| Tile 資料 | Banks 4-6 | Bank 7 |
| 排列表 | 0x1B0D4 (81 條) | 0x1ED14 (20 條) |

## 組件式結構

大眾臉頭像由三部分組成：
1. **共用框架** (頭盔、邊框) — 同 Group 內共用
2. **可替換組件** (眼睛、臉部、嘴巴) — 每個頭像不同
3. **Group 基底** — 決定 tile 資料的 ROM 位置

```
6×6 格子 Layout:
     C0  C1  C2  C3  C4  C5
    ┌───┬───┬───┬───┬───┬───┐
 R0 │ F │ F │ F │ F │ F │ F │  ← 框架 (共用)
    ├───┼───┼───┼───┼───┼───┤
 R1 │ F │ F │ F │ F │ F │ F │  ← 框架 (共用)
    ├───┼───┼───┼───┼───┼───┤
 R2 │ F │ E │ E │ E │ F │ F │  ← 眼睛區 (C1-C3 可替換)
    ├───┼───┼───┼───┼───┼───┤
 R3 │ F │ A │ A │ A │ F │ F │  ← 臉部區 (C1-C3 可替換)
    ├───┼───┼───┼───┼───┼───┤
 R4 │ F │ M │ M │ M │ F │ F │  ← 嘴巴上 (C1-C3 可替換)
    ├───┼───┼───┼───┼───┼───┤
 R5 │ F │ M │ M │ M │ F │ F │  ← 嘴巴下 (C1-C3 可替換)
    └───┴───┴───┴───┴───┴───┘

F = 框架 tile (固定)
E = 眼睛 tile (可替換)
A = 臉部 tile (可替換)
M = 嘴巴 tile (可替換)
```

## 資料結構定義

```
// 排列模板表 (20 條 × 36 bytes)
TEMPLATE_TABLE_ADDR = 0x1ED14

// 索引表 (每個 174 bytes，對應 P081-P254)
INDEX_TABLE_1 = 0x1EFE4    // 值範圍 0-4
INDEX_TABLE_2 = 0x1F092    // 值範圍 0-4
INDEX_TABLE_3 = 0x1F140    // 值範圍 0-4

// 變體資料位置
EYES_START   = 0x1DE14    // 20 組 × 3 tiles × 16 bytes = 960 bytes
FACES_START  = 0x1E1D4    // 20 組 × 3 tiles × 16 bytes = 960 bytes
MOUTHS_START = 0x1E594    // 20 組 × 6 tiles × 16 bytes = 1920 bytes

// 19 個 Group 定義 (ROM 偏移, Tile 數量)
GROUPS = [
    (0x1C194, 24),  // G00
    (0x1C314, 24),  // G01
    (0x1C494, 24),  // G02
    (0x1C614, 24),  // G03
    (0x1C794, 22),  // G04
    (0x1C914, 21),  // G05
    (0x1CA94, 20),  // G06
    (0x1CC14, 20),  // G07
    (0x1CD94, 21),  // G08
    (0x1CF14, 24),  // G09
    (0x1D094, 21),  // G10
    (0x1D214, 21),  // G11
    (0x1D394, 22),  // G12
    (0x1D514, 22),  // G13
    (0x1D694, 24),  // G14 (舊稱 Group A)
    (0x1D814, 24),  // G15
    (0x1D994, 24),  // G16
    (0x1DB14, 24),  // G17 (舊稱 Group D)
    (0x1DC94, 24),  // G18
]

// Group → Template 映射
// ⚠️ 待確認: T04 可能有被使用 (P138 高沛)，若屬實則此映射需調整
GROUP_TO_TEMPLATE = {
    0: 0, 1: 1, 2: 2, 3: 3,      // G00-G03 直接對應
    4: 5, 5: 6, 6: 7, 7: 8,      // G04+ 跳過 T04 (待確認)
    8: 9, 9: 10, 10: 11,
    11: 12, 12: 13, 13: 14,
    14: 15, 15: 16, 16: 17, 17: 18, 18: 19,
}

// 8 種 Pattern 類型
PATTERN_TYPES = {
    1: "標準 24-tile (max=23)",
    2: "tile 12 重複 (max=22)",
    3: "tile 13 重複 (max=20)",
    4: "tile 12 重複 (max=20)",
    5: "tile 0 重複 (max=19)",
    6: "tile 0 重複 (max=20)",
    7: "tile 13 重複 (max=21)",
    8: "tile 12 重複 (max=21)",
}

// Group → Pattern 映射
GROUP_TO_PATTERN = {
    0: 1, 1: 1, 2: 1, 3: 1,
    4: 2, 5: 3, 6: 4, 7: 5,
    8: 3, 9: 1, 10: 3,
    11: 6, 12: 7, 13: 8,
    14: 1, 15: 1, 16: 1, 17: 1, 18: 1,
}
```

## 步驟一: 判斷是否為大眾臉頭像

```
function is_mob_portrait(portrait_index):
    return portrait_index >= 81
```

## 步驟二: 獲取 Group 和變體索引 [待確認]

```
function get_mob_portrait_params(portrait_index):
    // 計算在索引表中的位置
    table_index = portrait_index - 81

    // 讀取三個索引表的值
    t1 = ROM[INDEX_TABLE_1 + table_index]  // 0-4
    t2 = ROM[INDEX_TABLE_2 + table_index]  // 0-4
    t3 = ROM[INDEX_TABLE_3 + table_index]  // 0-4

    // [待確認] 這三個值如何映射到 Group 和變體索引
    // 目前已知的映射關係不完全清楚
    // 可能需要額外的查表或計算

    return {
        table_values: [t1, t2, t3],
        // group, eye_idx, face_idx, mouth_idx 的計算方式待確認
    }
```

## 步驟三: 計算變體 Tile 編號

```
// 變體公式 (相對於 Group 基底)
function calculate_variant_tiles(eye_idx, face_idx, mouth_idx):
    // 眼睛: 3 tiles per variant, 20 variants (tiles 120-179)
    eye_base = 120 + eye_idx * 3
    eye_tiles = [eye_base, eye_base + 1, eye_base + 2]

    // 臉部: 3 tiles per variant, 20 variants (tiles 180-239)
    face_base = 180 + face_idx * 3
    face_tiles = [face_base, face_base + 1, face_base + 2]

    // 嘴巴: 6 tiles per variant, 20 variants (tiles 240-359)
    // 特殊排列: 2 rows × 3 cols
    mouth_base = 240 + mouth_idx * 6
    mouth_tiles = {
        row4: [mouth_base + 0, mouth_base + 1, mouth_base + 4],  // C1, C2, C3
        row5: [mouth_base + 2, mouth_base + 3, mouth_base + 5],  // C1, C2, C3
    }

    return { eye_tiles, face_tiles, mouth_tiles }
```

## 步驟四: 組合完整 Layout

```
function build_mob_layout(framework, eye_tiles, face_tiles, mouth_tiles):
    layout = copy(framework)

    // 填入眼睛 (Row 2, C1-C3)
    layout[2][1] = eye_tiles[0]
    layout[2][2] = eye_tiles[1]
    layout[2][3] = eye_tiles[2]

    // 填入臉部 (Row 3, C1-C3)
    layout[3][1] = face_tiles[0]
    layout[3][2] = face_tiles[1]
    layout[3][3] = face_tiles[2]

    // 填入嘴巴 (Row 4-5, C1-C3)
    layout[4][1] = mouth_tiles.row4[0]
    layout[4][2] = mouth_tiles.row4[1]
    layout[4][3] = mouth_tiles.row4[2]
    layout[5][1] = mouth_tiles.row5[0]
    layout[5][2] = mouth_tiles.row5[1]
    layout[5][3] = mouth_tiles.row5[2]

    return layout
```

## 步驟五: 載入 Tile 資料

```
function load_mob_tiles(group):
    base_addr = GROUP_BASES[group]

    // 載入足夠的 tiles (至少 360 個以涵蓋所有變體)
    tiles = []
    for i in range(400):
        tile_addr = base_addr + i * 16
        tile_data = ROM[tile_addr : tile_addr + 16]
        tiles.append(tile_data)

    return tiles
```

## 步驟六: 繪製頭像

```
function render_mob_portrait(portrait_index):
    // [待確認] 獲取 Group 和變體索引
    params = get_mob_portrait_params(portrait_index)
    group = params.group
    eye_idx = params.eye_idx
    face_idx = params.face_idx
    mouth_idx = params.mouth_idx

    // 計算變體 tiles
    variants = calculate_variant_tiles(eye_idx, face_idx, mouth_idx)

    // 獲取框架 (可能需要根據 Group 和模板類型選擇)
    framework = get_framework(group, params.template_type)

    // 組合完整 layout
    layout = build_mob_layout(framework,
                              variants.eye_tiles,
                              variants.face_tiles,
                              variants.mouth_tiles)

    // 載入 tile 資料
    tiles = load_mob_tiles(group)

    // 繪製 48×48 頭像
    canvas = new_canvas(48, 48)
    for row in range(6):
        for col in range(6):
            tile_num = layout[row][col]
            tile_data = tiles[tile_num]
            draw_tile(canvas, col * 8, row * 8, tile_data)

    return canvas
```

## 已驗證的範例

### P081 周泰 (Group A)

```
Group: A (基底 0x1D694)
eye_idx: 17, face_idx: 18, mouth_idx: 16

Layout:
[  0,   1,   4,   5,   8,   9],
[  2,   3,   6,   7,  10,  11],
[ 12, 171, 172, 173,  14,  15],  // 眼睛: 120 + 17*3 = 171
[ 13, 234, 235, 236,  16,  17],  // 臉部: 180 + 18*3 = 234
[ 18, 336, 337, 340,  20,  21],  // 嘴巴: 240 + 16*6 = 336
[ 19, 338, 339, 341,  22,  23],
```

### P082 孫翊 (Group A)

```
Group: A (基底 0x1D694)
eye_idx: 18, face_idx: 19, mouth_idx: 18

Layout:
[  0,   1,   4,   5,   8,   9],
[  2,   3,   6,   7,  10,  11],
[ 12, 174, 175, 176,  14,  15],  // 眼睛: 120 + 18*3 = 174
[ 13, 237, 238, 239,  16,  17],  // 臉部: 180 + 19*3 = 237
[ 18, 348, 349, 352,  20,  21],  // 嘴巴: 240 + 18*6 = 348
[ 19, 350, 351, 353,  22,  23],
```

### P083 孫瑜 (Group B)

```
Group: B (基底 0x1C194)
eye_idx: 2, face_idx: 1, mouth_idx: 2

// 注意: Group B 的變體 tile 編號需要加上 Group 偏移
Layout (相對於 Group B 基底):
[  0,   1,   4,   5,   8,   9],
[  2,   3,   6,   7,  10,  11],
[ 12, 462, 463, 464,  14,  15],  // 眼睛 (不同計算方式)
[ 13, 519, 520, 521,  16,  17],  // 臉部
[ 18, 588, 589, 592,  20,  21],  // 嘴巴
[ 19, 590, 591, 593,  22,  23],
```

## 已知的 Group 成員

| 新編號 | 舊編號 | 基底位址 | 已確認成員 |
|--------|--------|----------|------------|
| G00 | B | 0x1C194 | P083 孫瑜, P185 傅士仁, P186 周倉 |
| G05 | C | 0x1C914 | P131 法正, P165 張昭, P166 張紘, P204 韓玄, P211 鞏志 |
| G12 | E | 0x1D394 | P168 虞翻 |
| G14 | A | 0x1D694 | P081 周泰, P082 孫翊, P084 孫桓, P182 糜芳 |
| G17 | D | 0x1DB14 | P195 徐盛 |

## 索引表資料範例

```
portrait_index → (T1, T2, T3)

P081 周泰:    (0, 2, 0)
P082 孫翊:    (0, 0, 0)
P083 孫瑜:    (0, 2, 1)
P084 孫桓:    (0, 2, 1)  // 與 P083 相同，但不同 Group
P131 法正:    (3, 3, 4)
P165 張昭:    (1, 2, 0)
P182 糜芳:    (0, 3, 3)
```

## 已解決問題

1. **Group 框架系統**: 確認 19 個 Group (G00-G18) 的 ROM 位置
2. **Template 排列表**: 20 個 Template 於 0x1ED14 ~~(G04+ 跳過 T04)~~ (待確認)
3. **8 種 Pattern 類型**: 根據 tile 重複方式分類
4. **Group-Template-Pattern 映射**: 完整對照表已建立

## 待解決問題

1. **T04 是否被使用**: P138 高沛的變體 (E2, F3, M1) 找不到匹配的 Group，推測 T04 有被使用
   - 若屬實，則 Group 數量為 20 個 (G00-G19)，現有 G04+ 編號需遞增 1
2. **portrait_id → Group 映射**: 174 個大眾臉頭像如何對應到 19/20 個 Group？
   - 三個索引表 (T1, T2, T3) 與 Group 的關係待確認

2. **變體索引計算**: T1, T2, T3 如何轉換為 eye_idx, face_idx, mouth_idx？
   - 值範圍 0-4，但變體索引範圍是 0-19
   - 可能存在二級查表或公式

## 相關檔案

- `MEMORY.md` - 詳細的逆向工程研究記錄
- `docs/PORTRAIT_SYSTEM_PSEUDOCODE.md` - 標準頭像系統 pseudo code
- `tools/portrait_matcher.py` - 頭像匹配工具
- `tools/portrait_generator.py` - 頭像產生工具
- `mob_portrait/variant_explorer/explorer_standalone.html` - 大眾臉頭像互動探索器
