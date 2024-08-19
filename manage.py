import os
import sys
from ultralytics import YOLO

# Variáveis globais para armazenar os modelos
model_crop = None
model_letters = None

def load_models():
    global model_crop, model_letters
    model_crop = YOLO(os.path.join(os.path.dirname(__file__), 'plate/tipo_placa.pt'))
    model_letters = YOLO(os.path.join(os.path.dirname(__file__), 'plate/letras.pt'))

def main():
    """Função principal do Django."""
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
    load_models()

    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
