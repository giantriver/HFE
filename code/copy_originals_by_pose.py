#!/usr/bin/env python3
"""
Copy original images from data_origin/ to data_new/p1~p5
based on filenames that appear in data/p1~p5.

Also verifies image count consistency.

Requirements:
    pip install tqdm
"""

from pathlib import Path
import shutil
from tqdm import tqdm

# ==== 參數 ====
DATA_ORIGIN = Path("../../data_origin")      # 原圖資料夾
DATA_SKELETON = Path("../../data")           # 已畫骨架的資料夾(p1~p5)
DATA_NEW = Path("../../data_new")            # 要輸出的資料夾
POSE_CLASSES = [f"p{i}" for i in range(1, 6)]
# =============

def ensure_dirs():
    for cls in POSE_CLASSES:
        (DATA_NEW / cls).mkdir(parents=True, exist_ok=True)

def build_origin_index():
    """
    建立 {stem: Path} 對照表。
    若同一 stem 在 origin 裡有多個副檔名，以先出現者為主。
    """
    index = {}
    for img_path in DATA_ORIGIN.iterdir():
        if img_path.is_file():
            stem = img_path.stem
            index.setdefault(stem, img_path)
    return index

def main():
    ensure_dirs()
    origin_idx = build_origin_index()
    missing = []

    for cls in POSE_CLASSES:
        skel_dir = DATA_SKELETON / cls
        for skel_img in tqdm(list(skel_dir.glob("*")), desc=f"Copying {cls}"):
            stem = skel_img.stem
            origin_img = origin_idx.get(stem)
            if origin_img:
                dst = DATA_NEW / cls / origin_img.name
                if not dst.exists():
                    shutil.copy2(origin_img, dst)
            else:
                missing.append(skel_img.name)

    # === 比對張數 ===
    print("\n📊 每個姿勢類別張數比對：")
    total_correct = True
    for cls in POSE_CLASSES:
        n_skel = len(list((DATA_SKELETON / cls).glob("*")))
        n_new = len(list((DATA_NEW / cls).glob("*")))
        status = "✅" if n_skel == n_new else "❌"
        if n_skel != n_new:
            total_correct = False
        print(f"  {cls}: 原骨架圖 {n_skel:>4} 張，複製原圖 {n_new:>4} 張 {status}")

    print("\n🎯 全部比對完成。")
    if missing:
        print(f"❗ 找不到對應原圖的骨架圖共 {len(missing)} 張：")
        for name in missing:
            print("   ", name)
    elif total_correct:
        print("✅ 所有類別張數一致，原圖已成功對應並分類！")
    else:
        print("⚠️ 有些類別張數不一致，請檢查上方標記 ❌ 的項目。")

if __name__ == "__main__":
    main()
