import cv2
import numpy as np

from src.ia.base_model import BaseModel
from src.ia.utils import converto_image_to_b64, plot_boxes


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

    @classmethod
    def filter_items(cls, items, min_area_overlap=0.7):
        items_to_keep = []

        while items:
            item = items.pop(0)
            overlapping_items = [item]

            for other_item in items:
                if cls.area_overlap(item, other_item) >= min_area_overlap:
                    overlapping_items.append(other_item)

            best_item = max(overlapping_items, key=lambda x: x[1].item())
            items_to_keep.append(best_item)
            items = [i for i in items if i not in overlapping_items]

        return items_to_keep

    def predict(self, image_path: str, thumbs, **kwargs):
        plate, thumb, product = None, None, None
        
        def plate_rotation_or_not(product, image):
            if product in ['New Moto', 'Old Moto']:
                if product == 'Old Moto':
                    height_60_percent = int(0.70 * image.shape[0])
                    width_40_percent = int(0.50 * image.shape[0])
                    
                if product == 'New Moto':
                    height_60_percent = int(0.70 * image.shape[0])
                    width_40_percent = int(0.40 * image.shape[0])
                top_results_letras_placa = self.model_letters(image[:height_60_percent])
                bottom_results_letras_placa = self.model_letters(image[width_40_percent:])
                
                plate = get_plate(top_results_letras_placa, image, product, "top") + get_plate(bottom_results_letras_placa, image, product, "bottom")
            
            else:
                results_letras_placa = self.model_letters(image)
                plate = get_plate(results_letras_placa, image, product, "")
                plate = self.transform_plate(plate, product)
                
            return plate

        def get_plate(results_letras_placa, image, product, local) -> str:
            if product == 'New Moto':
                min_height_percent = 25
                
            if product == 'Old Moto':
                min_height_percent = 18
                
            results_letras_placa = results_letras_placa[0]
            image_height, image_width = image.shape[:2]
            detections = []

            iterator = zip(results_letras_placa.boxes.xyxy, results_letras_placa.boxes.cls, results_letras_placa.boxes.conf)
            for box, cls, conf in iterator:
                class_name = results_letras_placa.names[int(cls)]
                confidence = conf * 100
                x1, y1, x2, y2 = map(int, box)
                
                height = y2 - y1
                height_percent = (height / image_height) * 100
                
                if height_percent >= min_height_percent:
                    detections.append((class_name, confidence, (x1 + x2) / 2, x1, y1, x2, y2))
                    image = plot_boxes(image, box, class_name, confidence)

            # Ordenar as detecções pela distância ao centro da imagem
            center_x = image_width / 2
            detections.sort(key=lambda det: abs(det[2] - center_x))

            if local == "top":
                # Pegar as 3 mais próximas do centro
                selected_detections = sorted(detections, key=lambda det: abs(det[2] - center_x))
            elif local == "bottom":
                # Pegar as 4 mais próximas do centro
                selected_detections = sorted(detections, key=lambda det: abs(det[2] - center_x))
            else:
                selected_detections = detections  # Caso não seja "top" ou "bottom", mantém todas as detecções

            items_to_keep = self.filter_items(selected_detections)

            ordered_detections_by_x = sorted(items_to_keep, key=lambda x: x[2])  
            digits = [str(int(c[0])) if c[0].isnumeric() else c[0] for c in ordered_detections_by_x]
            return ''.join(digits)

        try:
            results_recorte_placa = self.model_crop(image_path)
            image, product = self.get_closest_items(image_path, results_recorte_placa)
            plate = plate_rotation_or_not(product, image)
            plate = self.transform_plate(plate, product)
            
            if thumbs:
                thumb = converto_image_to_b64(image)

        except Exception as exc:
            print("Falha ao ler placa::::: ", exc)
            
        finally:
            return {
                "result": plate or "Placa não reconhecida",
                "thumb": thumb,
                "product": product,
            } 
        
    @classmethod
    def transform_plate(cls, plate, type_product):
        if type_product == 'New Car':
            return cls.format_new_car(plate, type_product)

        elif type_product == 'Old Car':
            return cls.format_old_car(plate, type_product)
        
        else:
            return cls.format_io(plate, type_product)

    # @classmethod
    # def transform_string(cls, detections, type_product):
    #     ordered_detections_by_x = sorted(detections, key=lambda x: x[2])  
    #     digits = [str(int(c[0])) if c[0].isnumeric() else c[0] for c in ordered_detections_by_x]
    #     plate = ''.join(digits)

    #     if type_product == 'New Car':
    #         return cls.format_new_car(plate, type_product)

    #     elif type_product == 'Old Car':
    #         return cls.format_old_car(plate, type_product)
        
    #     else:
    #         return cls.format_io(plate, type_product)

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
