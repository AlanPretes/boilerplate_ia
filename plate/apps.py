import os
import logging
from django.apps import AppConfig
from ultralytics import YOLO

logger = logging.getLogger(__name__)

class PlateConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'plate'

    def ready(self):
        logger.info("Carregando modelos de IA...")
        # Carrega os modelos de IA uma vez quando o aplicativo é inicializado
        self.model_angle_car = YOLO(os.path.join(os.path.dirname(__file__), 'ias_models/angle_car_.pt'))
        self.model_type_vehicle = YOLO(os.path.join(os.path.dirname(__file__), 'ias_models/type_vehicle.pt'))
        self.model_crop_moto = YOLO(os.path.join(os.path.dirname(__file__), 'ias_models/tipo_placa_moto.pt'))
        self.model_crop_car = YOLO(os.path.join(os.path.dirname(__file__), 'ias_models/tipo_placa_car.pt'))
        self.model_letters_new_moto = YOLO(os.path.join(os.path.dirname(__file__), 'ias_models/letras_new_moto.pt'))
        self.model_letters_old_moto = YOLO(os.path.join(os.path.dirname(__file__), 'ias_models/letras_old_moto.pt'))
        self.model_letters_old_car_0_180 = YOLO(os.path.join(os.path.dirname(__file__), 'ias_models/letras_old_moto.pt'))
        self.model_letters_new_car_0_180 = YOLO(os.path.join(os.path.dirname(__file__), 'ias_models/letras_new_moto.pt'))
        self.model_letters_old_car_45_225 = YOLO(os.path.join(os.path.dirname(__file__), 'ias_models/letras_old_moto.pt'))
        self.model_letters_new_car_45_225 = YOLO(os.path.join(os.path.dirname(__file__), 'ias_models/letras_new_moto.pt'))
        self.model_letters_old_car_135_315 = YOLO(os.path.join(os.path.dirname(__file__), 'ias_models/letras_old_moto.pt'))
        self.model_letters_new_car_135_315 = YOLO(os.path.join(os.path.dirname(__file__), 'ias_models/letras_new_moto.pt'))
        logger.info("Modelos de IA carregados com sucesso.")
