import cv2
import numpy as np
import io
import base64
import cv2
from PIL import Image
from abc import ABC, abstractmethod
from io import BytesIO
from PIL import Image
from django.core.files import File
import uuid
from django.conf import settings
import os

def plot_boxes(image, box, label=None, confidence=None):
    x1, y1, x2, y2 = map(int, box)
    color = (0, 255, 0)  # Verde
    thickness = max(1, image.shape[1] // 400)
    cv2.rectangle(image, (x1, y1), (x2, y2), color, thickness)
    return image


def convert_image_to_b64(img, max_size=200):
    image = Image.fromarray(img)
    ratio = min(max_size / image.width, max_size / image.height)
    new_size = (int(image.width * ratio), int(image.height * ratio))
    resized_image = image.resize(new_size)

    buffer = io.BytesIO()
    resized_image.save(buffer, format='PNG')
    buffer.seek(0)
    thumb = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    return thumb


class BaseModel(ABC):
    @abstractmethod
    def predict(self, image_path: str, **kwargs):
        pass


class PanelAlerts(BaseModel):
    def __init__(self, model_airbag_icon):
        self.model_airbag_icon = model_airbag_icon
    
    def predict(self, image_path: str, image_name:str):
        airbag_icon = None
        thumb_url = "Erro ao criar thumb"
        save_path = image_path
        try:
            # Carregar imagem
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError("Erro ao carregar a imagem.")

            # Faz a predição usando o modelo de detecção airbag (YOLOv8)
            results = self.model_airbag_icon.predict(image)

            # Extraímos as detecções
            boxes = results[0].boxes.xyxy  # Coordenadas das caixas delimitadoras
            confidences = results[0].boxes.conf  # Confiança de cada predição
            class_indices = results[0].boxes.cls  # Índice das classes
            class_names = self.model_airbag_icon.names
            
            # Percorre cada detecção e processa se for o ícone airbag
            for box, cls_idx, confidence in zip(boxes, class_indices, confidences):
                label = class_names[int(cls_idx)]
                if label == "ABS":
                    airbag_icon = "Ícone AirBag detectado"
                    # Marcação da imagem com a caixa delimitadora e label
                    image = plot_boxes(image, box, label, confidence)
                    
                    # Gerar um nome aleatório para a imagem
                    path = f"images/panel/reconhecidas_airbag/{image_name}"
                    save_path = os.path.join(settings.MEDIA_ROOT, path)

                    # Criar pasta se não existir
                    os.makedirs(os.path.dirname(save_path), exist_ok=True)

                    # Salvar a imagem
                    cv2.imwrite(save_path, image) 
                    
                    thumb_url = os.path.join(settings.MEDIA_URL, path)
                    
        except Exception as e:
            airbag_icon = f"Erro: {str(e)}"
        finally:
            response = {
                "airbag_icon": airbag_icon or "Ícone Air Bag não detectado",
                "thumb": thumb_url,
            }
            return response