import os
import sys
from ultralytics import YOLO

# Variáveis globais para armazenar os modelos
model_angle_car = None
model_crop_moto = None
model_crop_car = None
model_letters_new_moto = None
model_letters_old_moto = None
model_letters_old_car_0_180 = None
model_letters_new_car_0_180 = None
model_letters_old_car_45_225 = None
model_letters_new_car_45_225 = None
model_letters_old_car_135_315 = None
model_letters_new_car_135_315 = None



def load_models():...
    # global model_crop_moto, model_crop_car, model_letters_new_moto, model_letters_old_moto, \
    # model_type_vehicle, model_angle_car, model_letters_old_car_0_180, model_letters_new_car_0_180,\
    # model_letters_old_car_45_225, model_letters_new_car_45_225, model_letters_old_car_135_315, \
    # model_letters_new_car_135_315
    
    # model_angle_car = YOLO(os.path.join(os.path.dirname(__file__), 'plate/ias_models/angle_car_.pt'))
    # model_type_vehicle = YOLO(os.path.join(os.path.dirname(__file__), 'plate/ias_models/type_vehicle.pt'))
    # model_crop_moto = YOLO(os.path.join(os.path.dirname(__file__), 'plate/ias_models/tipo_placa_moto.pt'))
    # model_crop_car = YOLO(os.path.join(os.path.dirname(__file__), 'plate/ias_models/tipo_placa_car.pt'))
    # model_letters_new_moto = YOLO(os.path.join(os.path.dirname(__file__), 'plate/ias_models/letras_new_moto__.pt'))
    # model_letters_old_moto = YOLO(os.path.join(os.path.dirname(__file__), 'plate/ias_models/letras_old_moto.pt'))
    # model_letters_old_car_0_180 = YOLO(os.path.join(os.path.dirname(__file__), 'plate/ias_models/letras_old_car_0_180.pt'))
    # model_letters_new_car_0_180 = YOLO(os.path.join(os.path.dirname(__file__), 'plate/ias_models/letras_new_car_0_180.pt'))
    # model_letters_old_car_45_225 = YOLO(os.path.join(os.path.dirname(__file__), 'plate/ias_models/letras_old_car_45_225.pt'))
    # model_letters_new_car_45_225 = YOLO(os.path.join(os.path.dirname(__file__), 'plate/ias_models/letras_new_car_45_225.pt'))
    # model_letters_old_car_135_315 = YOLO(os.path.join(os.path.dirname(__file__), 'plate/ias_models/letras_old_car_135_315.pt'))
    # model_letters_new_car_135_315 = YOLO(os.path.join(os.path.dirname(__file__), 'plate/ias_models/letras_new_car_135_315.pt'))

def main():

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    # Carrega os modelos de IA antes de iniciar o servidor
    # load_models()

    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
