import io
import base64

import cv2
from PIL import Image


def plot_boxes(image, box, label=None, confidence=None):
    x1, y1, x2, y2 = map(int, box)
    color = (0, 255, 0)  # Verde
    thickness = max(1, image.shape[1] // 400)
    cv2.rectangle(image, (x1, y1), (x2, y2), color, thickness)
    
    if label and confidence is not None:
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = max(0.5, image.shape[1] / 3000)
        font_thickness = max(1, image.shape[1] // 1000)
        label_size = cv2.getTextSize(label, font, font_scale, font_thickness)[0]
        
        label_x = max(0, min(x1, image.shape[1] - label_size[0]))
        label_y = y1 - 10 if y1 - 10 - label_size[1] > 0 else y2 + label_size[1] + 10
        
        cv2.rectangle(
            image, 
            (label_x, label_y - label_size[1]),
            (label_x + label_size[0], label_y + label_size[1] // 2), 
            color, 
            cv2.FILLED,
        )
        
        cv2.putText(
            image, 
            label, 
            (label_x, label_y), 
            font,
            font_scale, 
            (0, 0, 0), 
            font_thickness
        )
    
    return image


def converto_image_to_b64(img, max_size=200):
    image = Image.fromarray(img)
    ratio = min(max_size / image.width, max_size / image.height)
    new_size = (int(image.width * ratio), int(image.height * ratio))
    resized_image = image.resize(new_size)

    buffer = io.BytesIO()
    resized_image.save(buffer, format='PNG')
    buffer.seek(0)
    thumb = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    return thumb
