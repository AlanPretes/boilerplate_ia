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
    def __init__(self, model_type_vehicle, model_angle_car, model_crop_moto, model_crop_car,
        model_letters_new_moto, model_letters_old_moto,
        model_letters_old_car_0_180, model_letters_new_car_0_180,
        model_letters_old_car_45_225, model_letters_new_car_45_225,
        model_letters_old_car_135_315, model_letters_new_car_135_315):
    
        self.model_type_vehicle = model_type_vehicle
        self.model_angle_car = model_angle_car
        self.model_crop_moto = model_crop_moto
        self.model_crop_car = model_crop_car
        self.model_letters_new_moto = model_letters_new_moto
        self.model_letters_old_moto = model_letters_old_moto
        self.model_letters_old_car_0_180 = model_letters_old_car_0_180
        self.model_letters_new_car_0_180 = model_letters_new_car_0_180
        self.model_letters_old_car_45_225 = model_letters_old_car_45_225
        self.model_letters_new_car_45_225 = model_letters_new_car_45_225
        self.model_letters_old_car_135_315 = model_letters_old_car_135_315
        self.model_letters_new_car_135_315 = model_letters_new_car_135_315
        
        
    def type_vehicles(self, img_path, results):
        img = cv2.imread(img_path)
        img_height, img_width, _ = img.shape
        center_x, center_y = img_width / 2, img_height / 2

        closest_distance = float('inf')
        vehicle_type = None

        # Iterar sobre os resultados para encontrar o carro ou moto mais próximo do centro
        for result in results:
            for bbox in result.boxes:
                if bbox.cls in [2, 3]:  # Classe 2 para "car" e classe 3 para "motorcycle" no dataset COCO
                    # Verificar se a confiança é maior que 90%
                    if bbox.conf < 0.9:  # Confiança mínima de 90%
                        continue
                    
                    # Obter coordenadas da caixa delimitadora
                    x1, y1, x2, y2 = bbox.xyxy[0].cpu().numpy()
                    # Calcular o centro da caixa delimitadora
                    box_center_x = (x1 + x2) / 2
                    box_center_y = (y1 + y2) / 2

                    # Calcular a distância do centro da caixa até o centro da imagem
                    distance_to_center = np.sqrt((box_center_x - center_x) ** 2 + (box_center_y - center_y) ** 2)

                    # Verificar se essa caixa é a mais próxima do centro até agora
                    if distance_to_center < closest_distance:
                        closest_distance = distance_to_center
                        if bbox.cls == 2:
                            vehicle_type = "car"
                        elif bbox.cls == 3:
                            vehicle_type = "motorcycle"

        return vehicle_type if vehicle_type else "Nenhum veículo foi detectado"



    
    def get_closest_items(self, img_path, results):
        def euclidean_distance(x1, y1, x2, y2):
            return np.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

        img = cv2.imread(img_path)
        image_height, image_width = img.shape[:2]
        center_x, center_y = image_width / 2, image_height / 2
        
        distances = []
        
        for result in results:
            for bbox in result.boxes:
                x1, y1, x2, y2 = bbox.xyxy[0].cpu().numpy()
                item_center_x, item_center_y = (x1 + x2) / 2, (y1 + y2) / 2
                item_name = result.names[int(bbox.cls)]
                distance = euclidean_distance(item_center_x, item_center_y, center_x, center_y)
                distances.append((distance, item_name, (x1, y1, x2, y2)))
        
        distances.sort(key=lambda x: x[0])
        closest_items = distances[:1]
            
        if closest_items[0][1]:
            for distance, name, (x1, y1, x2, y2) in closest_items:
                cropped_img = img[int(y1):int(y2), int(x1):int(x2)]

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
    

    def predict(self, image_path: str, **kwargs):
        plate, thumb_top, thumb_bottom, product, labels_top, labels_bottom = None, None, None, None, [], []

        class_name = "Não aplicável"
        
        def plate_old_car_0_180(product, image):
            top_results_letras_placa = self.model_letters_old_car_0_180(image)
            top_labels = get_plate(top_results_letras_placa, image, product, "top")
            bottom_labels = None

            # Combina os resultados para formar a placa completa
            plate = top_labels['plate']

            return plate, top_labels['labels'], bottom_labels
        
        def plate_new_car_0_180(product, image):
            top_results_letras_placa = self.model_letters_old_car_0_180(image)
            top_labels = get_plate(top_results_letras_placa, image, product, "top")
            bottom_labels = None

            # Combina os resultados para formar a placa completa
            plate = top_labels['plate']

            return plate, top_labels['labels'], bottom_labels
        
        def plate_old_car_45_225(product, image):
            top_results_letras_placa = self.model_letters_old_car_45_225(image)
            top_labels = get_plate(top_results_letras_placa, image, product, "top")
            bottom_labels = None

            # Combina os resultados para formar a placa completa
            plate = top_labels['plate']

            return plate, top_labels['labels'], bottom_labels
        
        def plate_new_car_45_225(product, image):
            top_results_letras_placa = self.model_letters_new_car_45_225(image)
            top_labels = get_plate(top_results_letras_placa, image, product, "top")
            bottom_labels = None

            # Combina os resultados para formar a placa completa
            plate = top_labels['plate']

            return plate, top_labels['labels'], bottom_labels
        
        def plate_old_car_135_315(product, image):
            top_results_letras_placa = self.model_letters_old_car_135_315(image)
            top_labels = get_plate(top_results_letras_placa, image, product, "top")
            bottom_labels = None

            # Combina os resultados para formar a placa completa
            plate = top_labels['plate']

            return plate, top_labels['labels'], bottom_labels
        
        def plate_new_car_135_315(product, image):
            top_results_letras_placa = self.model_letters_new_car_135_315(image)
            top_labels = get_plate(top_results_letras_placa, image, product, "top")
            bottom_labels = None

            # Combina os resultados para formar a placa completa
            plate = top_labels['plate']

            return plate, top_labels['labels'], bottom_labels
        
        def plate_rotation_or_not_new_moto(product, image):
            height_70_percent = int(0.70 * image.shape[0])
            width_50_percent = int(0.50 * image.shape[0])

            # Processa a parte superior da imagem (70%)
            top_results_letras_placa = self.model_letters_new_moto(image[:height_70_percent])
            top_labels = get_plate(top_results_letras_placa, image[:height_70_percent], product, "top")

            # Processa a parte inferior da imagem (50%)
            bottom_results_letras_placa = self.model_letters_new_moto(image[width_50_percent:])
            bottom_labels = get_plate(bottom_results_letras_placa, image[width_50_percent:], product, "bottom")

            # Combina os resultados para formar a placa completa
            plate = top_labels['plate'] + bottom_labels['plate']

            return plate, top_labels['labels'], bottom_labels['labels']
        
        def plate_rotation_or_not_old_moto(product, image):
            height_70_percent = int(0.70 * image.shape[0])
            width_50_percent = int(0.50 * image.shape[0])

            # Processa a parte superior da imagem (70%)
            top_results_letras_placa = self.model_letters_old_moto(image[:height_70_percent])
            top_labels = get_plate(top_results_letras_placa, image[:height_70_percent], product, "top")

            # Processa a parte inferior da imagem (50%)
            bottom_results_letras_placa = self.model_letters_old_moto(image[width_50_percent:])
            bottom_labels = get_plate(bottom_results_letras_placa, image[width_50_percent:], product, "bottom")

            # Combina os resultados para formar a placa completa
            plate = top_labels['plate'] + bottom_labels['plate']

            return plate, top_labels['labels'], bottom_labels['labels']

        def get_plate(results_letras_placa, image, product, local) -> dict:
            if product is None:
                product = ""
            
            labels = []
            if product in ['New Moto', 'Old Moto']:
                min_height_percent = 30
            else:
                min_height_percent = 30
            
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
                    detections.append((class_name, conf, x1, y1, x2, y2))
                    # Salva as coordenadas no formato YOLO: [class, x_center, y_center, width, height]
                    x_center = ((x1 + x2) / 2) / image_width
                    y_center = ((y1 + y2) / 2) / image_height
                    width = (x2 - x1) / image_width
                    height = (y2 - y1) / image_height
                    labels.append([int(cls), x_center, y_center, width, height])

            # Filtrar sobreposições: manter apenas a detecção com maior accuracy
            filtered_detections = []
            for i, (class_name_i, conf_i, x1_i, y1_i, x2_i, y2_i) in enumerate(detections):
                is_max_conf = True
                for j, (class_name_j, conf_j, x1_j, y1_j, x2_j, y2_j) in enumerate(detections):
                    if i != j:
                        # Calcula a área de sobreposição
                        x_overlap = max(0, min(x2_i, x2_j) - max(x1_i, x1_j))
                        y_overlap = max(0, min(y2_i, y2_j) - max(y1_i, y1_j))
                        overlap_area = x_overlap * y_overlap
                        
                        # Calcula a área da caixa atual
                        box_area_i = (x2_i - x1_i) * (y2_i - y1_i)
                        overlap_percent = (overlap_area / box_area_i) * 100 if box_area_i > 0 else 0

                        # Verifica se a sobreposição é maior que 30% e se a detecção atual tem menor confidence
                        if overlap_percent > 30 and conf_i < conf_j:
                            is_max_conf = False
                            break

                if is_max_conf:
                    filtered_detections.append((class_name_i, (x1_i + x2_i) / 2, x1_i, y1_i, x2_i, y2_i))

            # Ordena as detecções filtradas pela posição horizontal (x) e monta a placa
            ordered_detections_by_x = sorted(filtered_detections, key=lambda x: x[1])
            digits = [str(int(c[0])) if c[0].isnumeric() else c[0] for c in ordered_detections_by_x]
            plate = ''.join(digits)

            return {'plate': plate, 'labels': labels}


        try:
            type_vehicle = self.model_type_vehicle(image_path)
                        
            results_type_vehicle = self.type_vehicles(image_path, type_vehicle)
            print(results_type_vehicle)
            
            if product == "New Car" or product == "Old Car":
                results_angle_car = self.model_angle_car(image_path)
                class_names = self.model_angle_car.names
                for result in results_angle_car:
                    for box in result.boxes:
                        class_id = int(box.cls)  # Índice da classe detectada
                        class_name = class_names[class_id]  # Nome da classe correspondente]
                        if class_name in ["0", "180"]:
                            results_recorte_placa = self.model_crop_car(image_path)
                            image, product = self.get_closest_items(image_path, results_recorte_placa)
                            if product == "New Car":
                                plate, labels_top, labels_bottom = plate_new_car_0_180(product, image)
                                plate = self.transform_plate(plate, product)
                            if product == "Old Car":
                                plate, labels_top, labels_bottom = plate_old_car_0_180(product, image)
                                plate = self.transform_plate(plate, product)
                        if class_name in ["45", "225"]:
                            results_recorte_placa = self.model_crop_car(image_path)
                            image, product = self.get_closest_items(image_path, results_recorte_placa)
                            if product == "New Car":
                                plate, labels_top, labels_bottom = plate_new_car_45_225(product, image)
                                plate = self.transform_plate(plate, product)
                            if product == "Old Car":
                                plate, labels_top, labels_bottom = plate_old_car_45_225(product, image)
                                plate = self.transform_plate(plate, product)
                        if class_name in ["135", "315"]:
                            results_recorte_placa = self.model_crop_car(image_path)
                            image, product = self.get_closest_items(image_path, results_recorte_placa)
                            if product == "New Car":
                                plate, labels_top, labels_bottom = plate_new_car_135_315(product, image)
                                plate = self.transform_plate(plate, product)
                            if product == "Old Car":
                                plate, labels_top, labels_bottom = plate_old_car_135_315(product, image)
                                plate = self.transform_plate(plate, product)

            else:
                results_recorte_placa = self.model_crop_moto(image_path)
                image, product = self.get_closest_items(image_path, results_recorte_placa)
                if product == "New Moto":
                    plate, labels_top, labels_bottom = plate_rotation_or_not_new_moto(product, image)
                    plate = self.transform_plate(plate, product)
                if product == "Old Moto":
                    plate, labels_top, labels_bottom = plate_rotation_or_not_old_moto(product, image)
                    plate = self.transform_plate(plate, product)
            
        except Exception as exc:
            product = "Produto não reconhecido"
            print("Falha ao ler placa::::: ", exc)           

        finally:
            return {
                "type_vehicle": results_type_vehicle if results_type_vehicle else "Tipo não reconhecido",
                "angle": class_name or "Não aplicável",
                "result": plate or "Placa não reconhecida",
                "product": product if product else None,
                "labels_top": labels_top if "Moto" in product else None,  # Retorna as coordenadas da parte superior para motos
                "labels_bottom": labels_bottom if "Moto" in product else None  # Retorna as coordenadas da parte inferior para motos
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
