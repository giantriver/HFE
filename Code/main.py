import cv2
import mediapipe as mp
import numpy as np
import time
import os

# 建立儲存資料夾
save_dir = "captured_images"
os.makedirs(save_dir, exist_ok=True)

# 初始化 MediaPipe
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()
mp_drawing = mp.solutions.drawing_utils


cap = cv2.VideoCapture('test2.mp4')

# 設定儲存間隔 (秒)
save_interval = 0.5
last_saved_time = time.time()

img_count = 0

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

        # 顯示角度
        cv2.putText(image, f'Elbow Angle: {int(elbow_angle)}', (50,50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,255,0), 2)
        cv2.putText(image, f'Shoulder Angle: {int(shoulder_angle)}', (50,80),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,255,0), 2)
        # 縮放視窗
        scale_percent = 50
        width = int(image.shape[1] * scale_percent / 100)
        height = int(image.shape[0] * scale_percent / 100)
        dim = (width, height)
        resized_image = cv2.resize(image, dim, interpolation=cv2.INTER_AREA)

        # 每隔 save_interval 秒儲存一張圖片
        current_time = time.time()
        if current_time - last_saved_time >= save_interval:
            save_path = os.path.join(save_dir, f"frame_{img_count:04d}.jpg")
            cv2.imwrite(save_path, image)
            print(f"Saved {save_path}")
            last_saved_time = current_time
            img_count += 1

    cv2.imshow('Pose Angle Detection', resized_image)

    # 按 q 鍵退出
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 釋放資源
cap.release()
cv2.destroyAllWindows()