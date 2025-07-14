import cv2
import mediapipe as mp
import numpy as np
import time
import os
from collections import defaultdict

# 建立儲存資料夾
save_dir = "captured_images"
os.makedirs(save_dir, exist_ok=True)

# 初始化 MediaPipe
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()
mp_drawing = mp.solutions.drawing_utils

cap = cv2.VideoCapture(r"C:\Mediapipe Genetate Dataset\MediaPipe_Pic_to_Video\Video\pushup.mp4")

# 取得影片fps, 初始化變數
fps = cap.get(cv2.CAP_PROP_FPS)
save_interval = 0.5  # 秒
save_every_n_frames = int(fps * save_interval)
frame_counter = 0
frame_duration = 1 / fps
img_count = 0

# 分類函式
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

# 計時相關變數
current_pose = None
start_time = None
pose_frame_counts = defaultdict(int)  # 每個動作累計張數

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
        def calculate_angle(a, b, c):
            ba = a - b
            bc = c - b
            cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
            angle = np.arccos(cosine_angle)
            return np.degrees(angle)

        elbow_angle = calculate_angle(shoulder, elbow, wrist)
        shoulder_angle = calculate_angle(hip, shoulder, elbow)

        # 動作分類
        pose_label = classify_pose(shoulder_angle, elbow_angle)

        pose_frame_counts[pose_label] += 1

        # 顯示角度與分類
        cv2.putText(image, f'Elbow: {int(elbow_angle)} Shoulder: {int(shoulder_angle)}',
                    (50,50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)
        cv2.putText(image, f'Pose: {pose_label}', (50,80),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,0,255), 2)

        # 每隔 save_interval 秒儲存一張圖片
        frame_counter += 1
        if frame_counter % save_every_n_frames == 0:
            save_path = os.path.join(save_dir, f"frame_{img_count:04d}_{pose_label}.jpg")
            cv2.imwrite(save_path, image)
            #print(f"Saved {save_path}")
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

# 程式結束 ➔ 紀錄最後一個動作
if current_pose is not None:
    # 每讀到一幀，就代表這個動作多維持了一 frame
    pose_frame_counts[current_pose] += 1
    print(f"{current_pose} 最後累計 frame 數: {pose_frame_counts[current_pose]}")

print("\n=== 每個動作的總計時間（依據影片 fps） ===")
for pose, count in pose_frame_counts.items():
    total_duration = count * frame_duration
    print(f"{pose}: {total_duration:.2f} 秒")

# 釋放資源
cap.release()
cv2.destroyAllWindows()
