import base64, io

import cv2
from PIL import Image

from src.ia.base_model import BaseModel
from src.ia.utils import converto_image_to_b64, plot_boxes


class AngleRecognitionModel(BaseModel):
    def __init__(self, model_angle):
        self.model_angle = model_angle

    def predict(self, image_path: str, thumbs, **kwargs):
        angle, thumb = None, None

        try:
            results = self.model_angle(image_path)
            image = cv2.imread(image_path)

            if results and len(results) > 0 and len(results[0].boxes) > 0:
                result = results[0]

                for _, (box, cls, conf) in enumerate(zip(result.boxes.xyxy, result.boxes.cls, result.boxes.conf)):
                    class_name = result.names[int(cls)]
                    confidence = conf * 100
                    if angle is None:
                        angle = class_name

                    image = plot_boxes(image, box, class_name, confidence)

                if thumbs:
                    thumb = converto_image_to_b64(image)
            
        finally:
            return {
                "result": angle or "Ângulo não reconhecido",
                "thumb": thumb
            } 
