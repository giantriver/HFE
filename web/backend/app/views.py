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
        """回傳兩個 3D 向量夾角 (deg)"""
        v1, v2 = np.array(v1), np.array(v2)
        cosang = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
        return np.degrees(np.arccos(np.clip(cosang, -1.0, 1.0)))

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

    def get_angles_and_score(self, lm, side, mp_pose):
        """side: 'LEFT' or 'RIGHT'"""
        SH = lm[getattr(mp_pose.PoseLandmark, f"{side}_SHOULDER").value]
        EL = lm[getattr(mp_pose.PoseLandmark, f"{side}_ELBOW").value]
        WR = lm[getattr(mp_pose.PoseLandmark, f"{side}_WRIST").value]
        HIP = lm[getattr(mp_pose.PoseLandmark, f"{side}_HIP").value]

        SH = [SH.x, SH.y, SH.z]
        EL = [EL.x, EL.y, EL.z]
        WR = [WR.x, WR.y, WR.z]
        HIP = [HIP.x, HIP.y, HIP.z]

        v_upper = np.array(EL) - np.array(SH)
        v_torso = np.array(HIP) - np.array(SH)
        theta_raise = self.angle_between(v_upper, v_torso)

        v_fore = np.array(WR) - np.array(EL)
        v_upper2 = np.array(SH) - np.array(EL)
        theta_elbow = self.angle_between(v_fore, v_upper2)

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
            pose = mp_pose.Pose(static_image_mode=True, model_complexity=1)
            
            results = pose.process(img_rgb)
            if not results.pose_landmarks:
                pose.close()
                return self.response_400("No pose detected in image")

            lm = results.pose_landmarks.landmark

            # Calculate scores for both arms
            left_info = self.get_angles_and_score(lm, 'LEFT', mp_pose)
            right_info = self.get_angles_and_score(lm, 'RIGHT', mp_pose)

            # Select best side
            best_side = 'LEFT' if left_info["score"] >= right_info["score"] else 'RIGHT'
            best_info = left_info if best_side == 'LEFT' else right_info

            # Draw pose landmarks with red, bold lines (excluding face)
            mp_drawing = mp.solutions.drawing_utils
            
            # Define connections excluding face landmarks (0-10 are face landmarks)
            body_connections = [
                connection for connection in mp_pose.POSE_CONNECTIONS
                if connection[0] > 10 and connection[1] > 10
            ]
            
            # Create a copy of pose landmarks with only body landmarks (11+)
            from mediapipe.framework.formats import landmark_pb2
            body_landmarks = landmark_pb2.NormalizedLandmarkList()
            
            # Copy only body landmarks (skip face landmarks 0-10)
            for i in range(11, len(results.pose_landmarks.landmark)):
                body_landmarks.landmark.append(results.pose_landmarks.landmark[i])
            
            # Adjust connections indices since we're skipping first 11 landmarks
            adjusted_connections = [
                (connection[0] - 11, connection[1] - 11) for connection in body_connections
            ]
            
            mp_drawing.draw_landmarks(
                img_bgr,
                body_landmarks,
                adjusted_connections,
                mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=8, circle_radius=8),  # Red landmarks, thicker
                mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=6)  # Red connections, bolder
            )

            # Add labels
            LEFT_WRIST = results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_WRIST.value]
            RIGHT_WRIST = results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_WRIST.value]

            h, w = img_bgr.shape[:2]
            left_pos = int(LEFT_WRIST.x * w), int(LEFT_WRIST.y * h)
            right_pos = int(RIGHT_WRIST.x * w), int(RIGHT_WRIST.y * h)

            cv2.putText(img_bgr, 'LEFT', left_pos, cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 100, 100), 3, cv2.LINE_AA)
            cv2.putText(img_bgr, 'RIGHT', right_pos, cv2.FONT_HERSHEY_SIMPLEX, 2, (100, 100, 255), 3, cv2.LINE_AA)

            # Add score label
            label = (f"{best_side} | {best_info['desc']} | "
                    f"θ_raise={best_info['theta_raise']:.1f}° | "
                    f"score={best_info['score']}")
            color = ((0, 255, 0) if best_info['score'] >= 7
                    else (0, 255, 255) if best_info['score'] >= 4
                    else (0, 0, 255))
            cv2.putText(img_bgr, label, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2, cv2.LINE_AA)

            # Convert processed image to base64
            _, buffer = cv2.imencode('.png', img_bgr)
            img_base64 = base64.b64encode(buffer).decode('utf-8')

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
