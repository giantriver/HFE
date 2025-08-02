import cv2
import mediapipe as mp
import numpy as np
import time
import os
from collections import defaultdict
import pandas as pd
from PIL import ImageFont, ImageDraw, Image

# ==========================
#  1. 初始化參數與資料夾
# ==========================

# 建立儲存資料夾
save_dir = "captured_images"
os.makedirs(save_dir, exist_ok=True)

# 初始化 MediaPipe
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()
mp_drawing = mp.solutions.drawing_utils

# 開啟影片
cap = cv2.VideoCapture(r"C:\Mediapipe Genetate Dataset\MediaPipe_Pic_to_Video\Video\work 1.mp4")
fps = cap.get(cv2.CAP_PROP_FPS)
frame_duration = 1 / fps

# 設定儲存間隔
save_interval = 0.5  # 秒
save_every_n_frames = int(fps * save_interval)
frame_counter = 0
img_count = 0

# 載入中文字型
font_path = "C:/Windows/Fonts/msjh.ttc"  # Windows 微軟正黑體
font = ImageFont.truetype(font_path, 40)

# ==========================
#  2. 動作分類函式
# ==========================
def calculate_angle(a, b, c):
    ba = a - b
    bc = c - b
    cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
    angle = np.arccos(cosine_angle)
    return np.degrees(angle)

def classify_pose(shoulder_angle, elbow_angle):
    if shoulder_angle > 90:
        return "手肘高於肩部"
    elif abs(shoulder_angle - 90) <= 10 and elbow_angle > 160:
        return "手肘與肩同高"
    elif abs(shoulder_angle - 90) <= 10 and abs(elbow_angle - 90) <= 10:
        return "手肘與肩同高，手臂彎曲90度"
    elif 10 <= shoulder_angle < 90:
        return "手臂與身體10~90度"
    elif shoulder_angle < 10:
        return "手臂貼近身體"
    else:
        return "其他"

# ==========================
#  3. 初始化計時與統計
# ==========================
pose_frame_counts = defaultdict(int)

# ==========================
#  4. 讀取影片逐幀處理
# ==========================
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # 轉換顏色
    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(image)
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    if results.pose_landmarks:
        mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
        landmarks = results.pose_landmarks.landmark

        # 取得關鍵點 (左側)
        shoulder = np.array([landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
                             landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y])
        elbow = np.array([landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x,
                          landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y])
        wrist = np.array([landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x,
                          landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y])
        hip = np.array([landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x,
                        landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y])

        # 計算角度
        elbow_angle = calculate_angle(shoulder, elbow, wrist)
        shoulder_angle = calculate_angle(hip, shoulder, elbow)

        # 動作分類
        pose_label = classify_pose(shoulder_angle, elbow_angle)

        # 累計動作 frame 數
        pose_frame_counts[pose_label] += 1

        # ➔ 用 PIL 畫中文
        image_pil = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(image_pil)
        draw.text((50, 50), f'手肘角度: {int(elbow_angle)}', font=font, fill=(0, 255, 0))
        draw.text((50, 100), f'肩膀角度: {int(shoulder_angle)}', font=font, fill=(0, 255, 0))
        draw.text((50, 150), f'動作: {pose_label}', font=font, fill=(255, 0, 0))
        image = cv2.cvtColor(np.array(image_pil), cv2.COLOR_RGB2BGR)

        # 每隔 save_interval 秒儲存一張圖片
        frame_counter += 1
        if frame_counter % save_every_n_frames == 0:
            save_path = os.path.join(save_dir, f"frame_{img_count:04d}_{pose_label}.jpg")
            cv2.imwrite(save_path, image)
            img_count += 1

    # 縮放視窗
    scale_percent = 50
    width = int(image.shape[1] * scale_percent / 100)
    height = int(image.shape[0] * scale_percent / 100)
    dim = (width, height)
    resized_image = cv2.resize(image, dim, interpolation=cv2.INTER_AREA)

    cv2.imshow('Pose Angle Detection', resized_image)

    # 按 q 鍵退出
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# ==========================
#  5. 結束後 ➔ 輸出統計結果
# ==========================

print("\n=== 每個動作的總計時間（依據影片 fps） ===")

all_pose_labels = [
    "手肘高於肩部",
    "手肘與肩同高",
    "手肘與肩同高，手臂彎曲90度",
    "手臂與身體10~90度",
    "手臂貼近身體"
]

pose_weights = {
    "手肘高於肩部": 7,
    "手肘與肩同高": 5,
    "手肘與肩同高，手臂彎曲90度": 4,
    "手臂與身體10~90度": 2,
    "手臂貼近身體": 1,
    "其他": 0
}

pose_results = []
total_weighted_score = 0
total_duration = 0

for pose in all_pose_labels:
    count = pose_frame_counts.get(pose, 0)
    duration_sec = count * frame_duration
    weight = pose_weights.get(pose, 0)
    weighted_score = weight * duration_sec

    total_weighted_score += weighted_score
    total_duration += duration_sec

    print(f"{pose}: 維持 {duration_sec:.2f} 秒")

    pose_results.append({
        "動作名稱": pose,
        "維持時間 (秒)": round(duration_sec, 2),
    })

if total_duration > 0:
    avg_score = total_weighted_score / total_duration
else:
    avg_score = 0

print(f"\n✅ 平均加權分數: {avg_score:.2f}")

# 系統評估級距顯示
if avg_score >= 6:
    rating = "負荷極高，應立即改善"
elif avg_score >= 4.5:
    rating = "負荷偏高，建議改善姿勢"
elif avg_score >= 3:
    rating = "負荷正常，可接受"
else:
    rating = "負荷低，良好狀態"

print(f"系統評估：{rating}")

pose_results.append({
    "動作名稱": "平均加權分數",
    "維持時間 (秒)": round(avg_score, 2),
})
pose_results.append({
    "動作名稱": "系統評估",
    "維持時間 (秒)": rating
})

# 輸出成 Excel
output_path = "pose_duration_results.xlsx"
df = pd.DataFrame(pose_results)
df.to_excel(output_path, index=False)
print(f"\n✅ 已將結果輸出到 {output_path}")

# ==========================
#  6. 釋放資源
# ==========================
cap.release()
cv2.destroyAllWindows()
