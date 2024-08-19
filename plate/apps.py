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
        self.model_crop = YOLO(os.path.join(os.path.dirname(__file__), './tipo_placa.pt'))
        self.model_letters = YOLO(os.path.join(os.path.dirname(__file__), './letras.pt'))
        logger.info("Modelos de IA carregados com sucesso.")
