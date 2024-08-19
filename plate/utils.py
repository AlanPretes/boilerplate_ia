import cv2
import numpy as np
import io
import base64
import cv2
from PIL import Image
from abc import ABC, abstractmethod

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


class BaseModel(ABC):
    @abstractmethod
    def predict(self, image_path: str, product: str, **kwargs):
        """Método abstrato para prever algo a partir de uma imagem."""
        pass


class PlateRecognitionModel(BaseModel):
    def __init__(self, model_crop, model_letters):
        self.model_crop = model_crop
        self.model_letters = model_letters

    def get_closest_items(self, img_path, results):
        def euclidean_distance(x1, y1, x2, y2):
            return np.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

        img = cv2.imread(img_path)
        image_height, image_width = img.shape[:2]
        center_x, center_y = image_width / 2, image_height / 2
        
        distances = []
        br = False
        
        for result in results:
            for bbox in result.boxes:
                x1, y1, x2, y2 = bbox.xyxy[0].cpu().numpy()
                item_center_x, item_center_y = (x1 + x2) / 2, (y1 + y2) / 2
                item_name = result.names[int(bbox.cls)]
                if item_name == 'BR':
                    br = True
                    continue
                distance = euclidean_distance(item_center_x, item_center_y, center_x, center_y)
                distances.append((distance, item_name, (x1, y1, x2, y2)))
        
        distances.sort(key=lambda x: x[0])
        closest_items = distances[:1]
            
        if closest_items[0][1]:
            for distance, name, (x1, y1, x2, y2) in closest_items:
                cropped_img = img[int(y1):int(y2), int(x1):int(x2)]

                if name == 'New Moto' and not br:
                    name = 'Old Moto'

                if name == 'New Car' and not br:
                    name = 'Old Car'

                return cropped_img, name
            
    @classmethod
    def area_overlap(cls, item1, item2):
        x1_1, y1_1, x2_1, y2_1 = item1[-4], item1[-3], item1[-2], item1[-1]
        x1_2, y1_2, x2_2, y2_2 = item2[-4], item2[-3], item2[-2], item2[-1]

        xi1 = max(x1_1, x1_2)
        yi1 = max(y1_1, y1_2)
        xi2 = min(x2_1, x2_2)
        yi2 = min(y2_1, y2_2)

        inter_width = max(0, xi2 - xi1 + 1)
        inter_height = max(0, yi2 - yi1 + 1)
        inter_area = inter_width * inter_height

        area1 = (x2_1 - x1_1 + 1) * (y2_1 - y1_1 + 1)
        area2 = (x2_2 - x1_2 + 1) * (y2_2 - y1_2 + 1)

        iou = inter_area / float(area1 + area2 - inter_area)
        
        return iou
    

    def predict(self, image_path: str, thumbs, **kwargs):
        plate, thumb_top, thumb_bottom, product, labels_top, labels_bottom = None, None, None, None, [], []
        
        def plate_rotation_or_not(product, image):
            height_70_percent = int(0.70 * image.shape[0])
            width_50_percent = int(0.50 * image.shape[0])
            
            # Processa a parte superior da imagem (70%)
            top_results_letras_placa = self.model_letters(image[:height_70_percent])
            top_labels = get_plate(top_results_letras_placa, image[:height_70_percent], product, "top")
            
            # Processa a parte inferior da imagem (50%)
            bottom_results_letras_placa = self.model_letters(image[width_50_percent:])
            bottom_labels = get_plate(bottom_results_letras_placa, image[width_50_percent:], product, "bottom")
            
            # Combina os resultados para formar a placa completa
            plate = top_labels['plate'] + bottom_labels['plate']

            return plate, top_labels['labels'], bottom_labels['labels']

        def get_plate(results_letras_placa, image, product, local) -> dict:
            labels = []
            if product == 'New Moto':
                min_height_percent = 40
                
            elif product == 'Old Moto':
                min_height_percent = 40
                
            else:
                min_height_percent = 50
                
            results_letras_placa = results_letras_placa[0]
            image_height, image_width = image.shape[:2]
            detections = []

            iterator = zip(results_letras_placa.boxes.xyxy, results_letras_placa.boxes.cls, results_letras_placa.boxes.conf)
            for box, cls, conf in iterator:
                class_name = results_letras_placa.names[int(cls)]
                x1, y1, x2, y2 = map(int, box)
                
                height = y2 - y1
                height_percent = (height / image_height) * 100
                
                if height_percent >= min_height_percent:
                    detections.append((class_name, (x1 + x2) / 2, x1, y1, x2, y2))
                    # image = plot_boxes(image, box, class_name)
                    
                    # Salva as coordenadas no formato YOLO: [class, x_center, y_center, width, height]
                    x_center = ((x1 + x2) / 2) / image_width
                    y_center = ((y1 + y2) / 2) / image_height
                    width = (x2 - x1) / image_width
                    height = (y2 - y1) / image_height
                    labels.append([int(cls), x_center, y_center, width, height])

            ordered_detections_by_x = sorted(detections, key=lambda x: x[1])  
            digits = [str(int(c[0])) if c[0].isnumeric() else c[0] for c in ordered_detections_by_x]
            plate = ''.join(digits)
            
            return {'plate': plate, 'labels': labels}

        try:
            results_recorte_placa = self.model_crop(image_path)
            image, product = self.get_closest_items(image_path, results_recorte_placa)
            plate, labels_top, labels_bottom = plate_rotation_or_not(product, image)
            plate = self.transform_plate(plate, product)
            
            if thumbs:
                thumb_top = converto_image_to_b64(image[:int(0.70 * image.shape[0])])  # Parte superior
                thumb_bottom = converto_image_to_b64(image[int(0.50 * image.shape[0]):])  # Parte inferior
            
        except Exception as exc:
            print("Falha ao ler placa::::: ", exc)
            
        finally:
            return {
                "result": plate or "Placa não reconhecida",
                "thumb_top": thumb_top,
                "thumb_bottom": thumb_bottom,
                "product": product,
                "labels_top": labels_top,  # Retorna as coordenadas da parte superior
                "labels_bottom": labels_bottom  # Retorna as coordenadas da parte inferior
            }
        
    @classmethod
    def transform_plate(cls, plate, type_product):
        if type_product == 'New Car':
            return cls.format_new_car(plate, type_product)

        elif type_product == 'Old Car':
            return cls.format_old_car(plate, type_product)
        
        else:
            return cls.format_io(plate, type_product)

    @classmethod
    def format_new_car(cls, plate: str, type_product: str):
        print("Formantando placa new_car: ", plate)
        return cls.format_io(plate, type_product)

    @classmethod
    def format_old_car(cls, plate: str, type_product: str):
        print("Formantando placa old_car: ", plate)
        return cls.format_io(plate, type_product)

    @classmethod
    def format_io(cls, plate: str, type_product: str) -> str:
        print("Formantando IOs para: ", type_product, plate)

        def get_char(plate, index, type) -> str:
            try:
                replace_ios = lambda char: { 'i': '1',  'o': '0', 'B': '8' }.get(char, char)
                replace_10s = lambda char: { '1': 'I',  '0': 'O', 'i': 'I', 'o': 'O', '8': 'B'  }.get(char, char)
                
                if index in [0, 1, 2]:
                    return replace_10s(plate[index])
                
                elif index == 4 and type in ['Old Car', 'Old Moto']:
                    return replace_ios(plate[index])
                
                elif index == 4 and type in ['New Car', 'New Moto']:
                    return replace_10s(plate[index])
                
                else:
                    return replace_ios(plate[index])
                
            except:
                return ''

        return ''.join([
            get_char(plate, 0, type_product),
            get_char(plate, 1, type_product),
            get_char(plate, 2, type_product),
            get_char(plate, 3, type_product),
            get_char(plate, 4, type_product),
            get_char(plate, 5, type_product),
            get_char(plate, 6, type_product),
        ])
