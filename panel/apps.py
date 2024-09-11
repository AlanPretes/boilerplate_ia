import os
import logging
from django.apps import AppConfig
from ultralytics import YOLO

logger = logging.getLogger(__name__)

class PanelConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'panel'

    def ready(self):
        logger.info("Carregando modelos de IA...")
        # Carrega os modelos de IA uma vez quando o aplicativo é inicializado
        self.model_airbag_icon = YOLO(os.path.join(os.path.dirname(__file__), 'ias_models/airbag_icon.pt'))
        logger.info("Modelos de IA carregados com sucesso.")