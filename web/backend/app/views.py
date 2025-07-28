from flask import render_template, request, jsonify
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder import ModelView, ModelRestApi
from flask_appbuilder.api import BaseApi, expose
import cv2
import mediapipe as mp
import numpy as np
import base64
from io import BytesIO
from PIL import Image

from . import appbuilder, db

"""
    Create your Model based REST API::

    class MyModelApi(ModelRestApi):
        datamodel = SQLAInterface(MyModel)

    appbuilder.add_api(MyModelApi)


    Create your Views::


    class MyModelView(ModelView):
        datamodel = SQLAInterface(MyModel)


    Next, register your Views::


    appbuilder.add_view(
        MyModelView,
        "My View",
        icon="fa-folder-open-o",
        category="My Category",
        category_icon='fa-envelope'
    )
"""

"""
    Application wide 404 error handler
"""


@appbuilder.app.errorhandler(404)
def page_not_found(e):
    return (
        render_template(
            "404.html", base_template=appbuilder.base_template, appbuilder=appbuilder
        ),
        404,
    )


class PoseAnalysisApi(BaseApi):

    def angle_between(self, v1, v2):
        """回傳兩個 3D 向量夾角 (deg) - matching check.py implementation"""
        v1 = np.array(v1)
        v2 = np.array(v2)

        dot = np.dot(v1, v2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)

        if norm1 == 0 or norm2 == 0:
            return 0

        cos = np.clip(dot / (norm1 * norm2), -1.0, 1.0)
        angle_rad = np.arccos(cos)
        angle_deg = np.degrees(angle_rad)

        return angle_deg

    def get_posture_score(self, theta_raise, theta_elbow):
        """根據抬舉角 θ_raise、肘彎曲 θ_elbow → (描述, 分數)"""
        if theta_raise >= 170:
            return "θ_raise ≥ 170°", 10
        if 100 < theta_raise < 170:
            return "90° < θ_raise < 170°", 7
        if 80 <= theta_raise <= 100:
            return ("θ_raise ≈ 90°，肘伸直" if theta_elbow >= 150
                    else "θ_raise ≈ 90°，肘彎曲"), 5 if theta_elbow >= 150 else 4
        if 10 <= theta_raise < 80:
            return "10° ≤ θ_raise < 80°", 2
        if theta_raise < 10:
            return "θ_raise < 10°", 1
        return "未定義姿勢", 0

    def get_angles_and_score(self, lm, side, mp_pose, img_width, img_height):
        """side: 'LEFT' or 'RIGHT', with proper scaling based on image dimensions"""
        SH = lm[getattr(mp_pose.PoseLandmark, f"{side}_SHOULDER").value]
        EL = lm[getattr(mp_pose.PoseLandmark, f"{side}_ELBOW").value]
        WR = lm[getattr(mp_pose.PoseLandmark, f"{side}_WRIST").value]
        HIP = lm[getattr(mp_pose.PoseLandmark, f"{side}_HIP").value]

        # Scale coordinates by image dimensions (matching check.py approach)
        SH_vec = np.array([img_width * SH.x, img_height * SH.y, img_width * SH.z])
        EL_vec = np.array([img_width * EL.x, img_height * EL.y, img_width * EL.z])
        WR_vec = np.array([img_width * WR.x, img_height * WR.y, img_width * WR.z])
        HIP_vec = np.array([img_width * HIP.x, img_height * HIP.y, img_width * HIP.z])

        # Output vectors for debugging
        print(f"{side}_SHOULDER vector: {SH_vec}")
        print(f"{side}_ELBOW vector: {EL_vec}")
        print(f"{side}_WRIST vector: {WR_vec}")
        print(f"{side}_HIP vector: {HIP_vec}")

        # Calculate vectors between scaled coordinates
        shoulder_to_elbow = EL_vec - SH_vec
        shoulder_to_hip = HIP_vec - SH_vec
        theta_raise = self.angle_between(shoulder_to_elbow, shoulder_to_hip)

        elbow_to_wrist = WR_vec - EL_vec
        elbow_to_shoulder = SH_vec - EL_vec
        theta_elbow = self.angle_between(elbow_to_wrist, elbow_to_shoulder)

        desc, score = self.get_posture_score(theta_raise, theta_elbow)
        return {
            "theta_raise": theta_raise,
            "theta_elbow": theta_elbow,
            "desc": desc,
            "score": score
        }

    @expose('/analyze', methods=['POST'])
    def analyze_pose(self):
        try:
            if 'image' not in request.files:
                return self.response_400("No image file provided")

            file = request.files['image']
            if file.filename == '':
                return self.response_400("No image file selected")

            # Read image
            image = Image.open(file.stream)
            img_array = np.array(image)

            # Convert to BGR for OpenCV
            if len(img_array.shape) == 3 and img_array.shape[2] == 3:
                img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                img_rgb = img_array
            else:
                return self.response_400("Invalid image format")

            # MediaPipe Pose processing
            mp_pose = mp.solutions.pose
            pose = mp_pose.Pose(static_image_mode=True, model_complexity=2)

            results = pose.process(img_rgb)
            if not results.pose_landmarks:
                pose.close()
                return self.response_400("No pose detected in image")

            lm = results.pose_landmarks.landmark

            # Get image dimensions
            h, w = img_rgb.shape[:2]

            # Calculate scores for both arms with proper scaling
            left_info = self.get_angles_and_score(lm, 'LEFT', mp_pose, w, h)
            right_info = self.get_angles_and_score(lm, 'RIGHT', mp_pose, w, h)

            # Select best side
            best_side = 'LEFT' if left_info["score"] >= right_info["score"] else 'RIGHT'
            best_info = left_info if best_side == 'LEFT' else right_info

            # Draw pose landmarks and connections (simplified approach like check.py)
            mp_drawing = mp.solutions.drawing_utils

            # Draw all pose landmarks and connections
            mp_drawing.draw_landmarks(
                img_bgr,
                results.pose_landmarks,
                mp_pose.POSE_CONNECTIONS,
                mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=4, circle_radius=6),  # Green landmarks
                mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=4)  # Red connections
            )

            # Add detailed landmark labels (matching check.py)
            keypoints_to_show = {
                "L_SH": mp_pose.PoseLandmark.LEFT_SHOULDER.value,
                "L_EL": mp_pose.PoseLandmark.LEFT_ELBOW.value,
                "L_WR": mp_pose.PoseLandmark.LEFT_WRIST.value,
                "L_HIP": mp_pose.PoseLandmark.LEFT_HIP.value,
                "R_SH": mp_pose.PoseLandmark.RIGHT_SHOULDER.value,
                "R_EL": mp_pose.PoseLandmark.RIGHT_ELBOW.value,
                "R_WR": mp_pose.PoseLandmark.RIGHT_WRIST.value,
                "R_HIP": mp_pose.PoseLandmark.RIGHT_HIP.value,
            }

            # Draw detailed labels with coordinates (matching check.py)
            landmarks = results.pose_landmarks.landmark
            for label, idx in keypoints_to_show.items():
                lm = landmarks[idx]
                x_px = int(lm.x * w)
                y_px = int(lm.y * h)
                z_val = lm.z

                text = f"{label} ({lm.x:.2f}, {lm.y:.2f}, {z_val:.2f})"
                cv2.putText(img_bgr, text, (x_px + 5, y_px - 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 255), 5)
                cv2.circle(img_bgr, (x_px, y_px), 6, (0, 255, 0), -1)

            # Add score label with both arms info for debugging
            label1 = (f"LEFT: θ_raise={left_info['theta_raise']:.1f}° θ_elbow={left_info['theta_elbow']:.1f}° score={left_info['score']}")
            label2 = (f"RIGHT: θ_raise={right_info['theta_raise']:.1f}° θ_elbow={right_info['theta_elbow']:.1f}° score={right_info['score']}")
            label3 = (f"BEST: {best_side} | {best_info['desc']}")

            color = ((0, 255, 0) if best_info['score'] >= 7
                    else (255, 255, 0) if best_info['score'] >= 4
                    else (0, 0, 255))

            cv2.putText(img_bgr, label1, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(img_bgr, label2, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(img_bgr, label3, (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2, cv2.LINE_AA)

            # Convert BGR back to RGB for proper web display
            img_rgb_final = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

            # Use PIL to encode as PNG (handles RGB correctly)
            pil_image = Image.fromarray(img_rgb_final)
            buffer = BytesIO()
            pil_image.save(buffer, format='PNG')
            img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

            pose.close()

            return self.response(200,
                left_arm=left_info,
                right_arm=right_info,
                best_side=best_side,
                best_score=best_info,
                processed_image=f"data:image/png;base64,{img_base64}"
            )

        except Exception as e:
            return self.response_500(f"Error processing image: {str(e)}")


appbuilder.add_api(PoseAnalysisApi)

db.create_all()
