import os
import tempfile
import logging

os.environ['MPLCONFIGDIR'] = tempfile.gettempdir()
os.environ['YOLO_CONFIG_DIR'] = tempfile.gettempdir()

from flask import Flask
from ultralytics import YOLO

from src.configs.database import db
from src.configs.migrations import migrate
from src.configs.auth import basic_auth
from src.configs.logger import logger
from src.configs.settings import Settings
from src.ia.plate_recog import PlateRecognitionModel
from src.views.api import api_router
from src.views.front import front_router


logger.info("Carregando modelo...")
model_crop = YOLO(os.path.join(os.path.dirname(__file__), 'ia/models/modelo_placa_v2.pt'))
model_letters = YOLO(os.path.join(os.path.dirname(__file__), 'ia/models/letras_placa.pt'))
plate_recognition_model = PlateRecognitionModel(model_crop, model_letters)

def create_app():
    logger.info("Carregando configurações do Flask...")
    app = Flask(__name__)
    app.config.from_object(Settings)
    
    logger.info("Iniciando banco de dados...")
    db.init_app(app)
    migrate.init_app(app, db)
    basic_auth.init_app(app)

    logger.info("Registrando Blueprints...")
    app.register_blueprint(api_router(db, plate_recognition_model))
    app.register_blueprint(front_router(db, plate_recognition_model))

    from src.models.log_model import LogModel

    logger.info("Todas as configurações realizadas com sucesso!")
    return app
