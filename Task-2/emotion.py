from deepface import DeepFace

class ExpressionDetection:
    def __init__(self):
        # You can change this to 'mediapipe' for speed, or 'mtcnn', 'ssd', etc.
        self.detector_backend = 'retinaface'  

    def detect_image_expression(self, image_pth: str) -> str:
        try:
            # Analyze emotions using DeepFace
            result = DeepFace.analyze(
                img_path=image_pth,
                actions=['emotion'],
                enforce_detection=True,
                detector_backend=self.detector_backend
            )

            # If multiple faces are detected, take the first one
            if isinstance(result, list) and result:
                dominant_emotion = result[0]['dominant_emotion']
            else:
                dominant_emotion = result['dominant_emotion']

            return dominant_emotion

        except ValueError as ve:
            if "Face could not be detected" in str(ve):
                return "No face detected in the image."
            else:
                return f"Error: {ve}"

        except Exception as err:
            return f"Unexpected error: {err}"
