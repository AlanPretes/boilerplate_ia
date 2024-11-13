import os
import tempfile
from datetime import datetime
from PIL import Image

import requests
from django.shortcuts import render, redirect
from django.urls import reverse
from django.apps import apps 
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.core.paginator import Paginator

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from plate.models import PlateModel
from plate.utils import PlateRecognitionModel


@login_required
def index(request):
    queryset = PlateModel.objects.all().order_by('-id')
    paginator = Paginator(queryset, 10)
    logs = paginator.get_page(int(request.GET.get('page', 1)))

    context = {
        'logs': logs,
    }

    return render(request, 'plate/index.html', context)

@login_required
def new(request):
    if request.method == 'POST':
        start = datetime.now()
        identifier = request.POST.get('identifier')
        plate = str(request.POST.get('plate')).upper()
        files = request.FILES.getlist('file')  # Obter todos os arquivos        

        for file in files:
            new_plate = PlateModel(
                identifier=str(identifier),
                plate=str(plate),
                product="",
                runtime=0.0
            )

            new_plate.save()
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
                for chunk in file.chunks():
                    temp_file.write(chunk)
                image_path = temp_file.name

            app_config = apps.get_app_config('plate')
            model_angle_car = app_config.model_angle_car
            model_crop_moto = app_config.model_crop_moto
            model_crop_car = app_config.model_crop_car
            model_letters_new_moto = app_config.model_letters_new_moto
            model_letters_old_moto = app_config.model_letters_old_moto
            model_letters_old_car_0_180 = app_config.model_letters_old_car_0_180
            model_letters_new_car_0_180 = app_config.model_letters_new_car_0_180
            model_letters_old_car_45_225 = app_config.model_letters_old_car_45_225 
            model_letters_new_car_45_225 = app_config.model_letters_new_car_45_225 
            model_letters_old_car_135_315 = app_config.model_letters_old_car_135_315
            model_letters_new_car_135_315 = app_config.model_letters_new_car_135_315
            model_type_vehicle = app_config.model_type_vehicle
            plate_recognition_model = PlateRecognitionModel(model_type_vehicle, model_angle_car,
                model_crop_moto, model_crop_car, model_letters_new_moto, model_letters_old_moto,
                model_letters_old_car_0_180, model_letters_new_car_0_180, model_letters_old_car_45_225,
                model_letters_new_car_45_225, model_letters_old_car_135_315, model_letters_new_car_135_315)

            # Faz a predição usando o caminho da imagem salva
            result = plate_recognition_model.predict(image_path)
            
            if result.get('result') != plate and result.get('product') in ['New Moto', 'Old Moto']:
                image = Image.open(image_path)
                rotated_image = image.rotate(-12, expand=True)  # Use -12 para girar em sentido horário
                rotated_image.save(image_path)
                result = plate_recognition_model.predict(image_path)
                

            # Associa o resultado ao modelo PlateModel
            new_plate.type_vehicle = result.get('type_vehicle')
            new_plate.angle = result.get('angle')
            new_plate.product = result.get('product', 'Produto Desconhecido')
            new_plate.labels_top = result.get('labels_top', [])
            new_plate.labels_bottom = result.get('labels_bottom', [])
            new_plate.result = result.get('result', 'Placa não reconhecida')

            if result['result'] == plate:
                new_plate.match = True

            new_plate.runtime = (datetime.now() - start).total_seconds()
            new_plate.save()
            
            if os.path.exists(image_path):
                os.remove(image_path)

        return redirect(reverse('plate:index'))
    
    return render(request, 'plate/new.html')


def generate_yolo_txt(plate_model, label_type):
    """
    Gera o conteúdo do arquivo .txt no formato YOLO com base nas coordenadas.
    `label_type` deve ser 'top' ou 'bottom' para gerar o arquivo correspondente.
    """
    lines = []
    labels = plate_model.labels_top if label_type == 'top' else plate_model.labels_bottom

    for label in labels:
        class_id, x_center, y_center, width, height = label
        lines.append(f"{class_id} {x_center} {y_center} {width} {height}")

    return "\n".join(lines)


@csrf_exempt 
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def new_plate_api(request):
    start = timezone.now()
    identifier = request.data.get('identifier')
    plate = str(request.data.get('plate')).upper()
    image_url = request.data.get('image_url')

    if not image_url:
        return Response({'error': 'Image URL is required.'}, status=status.HTTP_400_BAD_REQUEST)

    # Baixar a imagem da URL
    response = requests.get(image_url)
    if response.status_code != 200:
        return Response({'error': 'Failed to download image.'}, status=status.HTTP_400_BAD_REQUEST)

    # Criar um arquivo temporário a partir da imagem baixada
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
        temp_file.write(response.content)
        image_path = temp_file.name

    # Inicializa o modelo de reconhecimento de placas
    app_config = apps.get_app_config('plate')
    plate_recognition_model = initialize_plate_recognition_model(app_config)

    # Criar um novo modelo de placa sem salvar a imagem no banco de dados
    new_plate = PlateModel(
        identifier=str(identifier),
        plate=str(plate),
        product="",
        runtime=0.0
    )
    
    new_plate.save()

    # Faz a predição usando o caminho da imagem salva
    result = plate_recognition_model.predict(image_path)
    
    if result.get('result') != plate and result.get('product') in ['New Moto', 'Old Moto']:
        image = Image.open(image_path)
        rotated_image = image.rotate(-12, expand=True)  # Use -12 para girar em sentido horário
        rotated_image.save(image_path)
        result = plate_recognition_model.predict(image_path)
    
    new_plate.type_vehicle = result.get('type_vehicle')
    new_plate.angle = result.get('angle')
    new_plate.product = result.get('product', 'Produto Desconhecido')
    new_plate.labels_top = result.get('labels_top', [])
    new_plate.labels_bottom = result.get('labels_bottom', [])
    new_plate.result = result.get('result', 'Placa não reconhecida')
    new_plate.match = result['result'] == plate
    new_plate.runtime = (timezone.now() - start).total_seconds()
    
    new_plate.save()

    # Limpeza do arquivo temporário
    cleanup_temp_file(image_path)

    # Preparar os dados de resposta
    response_data = {
        "identificador": identifier,
        "type_vehicle": new_plate.type_vehicle,
        "angle": new_plate.angle,
        "tipo_placa": new_plate.product,
        "placa_fornecida": plate,
        "result_placa": new_plate.result,
        "match_placa": new_plate.match,
        "runtime": new_plate.runtime
    }

    return Response(response_data, status=status.HTTP_201_CREATED)

def initialize_plate_recognition_model(app_config):
    return PlateRecognitionModel(
        app_config.model_type_vehicle,
        app_config.model_angle_car,
        app_config.model_crop_moto,
        app_config.model_crop_car,
        app_config.model_letters_new_moto,
        app_config.model_letters_old_moto,
        app_config.model_letters_old_car_0_180,
        app_config.model_letters_new_car_0_180,
        app_config.model_letters_old_car_45_225,
        app_config.model_letters_new_car_45_225,
        app_config.model_letters_old_car_135_315,
        app_config.model_letters_new_car_135_315,
    )

def cleanup_temp_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)


@login_required
def resultados_view(request):
    # New Moto
    plates_to_exclude = ["YYY9999", "YYY0000", "YYY000", "YYY0002", "YYY0003"]
    new_moto_match_count = PlateModel.objects.filter(match=True, product="New Moto").exclude(plate__in=plates_to_exclude).count()
    new_moto_no_match_count = PlateModel.objects.filter(match=False, product="New Moto").exclude(plate__in=plates_to_exclude).count()
    new_moto_total = new_moto_match_count + new_moto_no_match_count
    new_moto_accuracy = (new_moto_match_count / new_moto_total) * 100 if new_moto_total > 0 else 0

    # Old Moto
    old_moto_match_count = PlateModel.objects.filter(match=True, product="Old Moto").count()
    old_moto_no_match_count = PlateModel.objects.filter(match=False, product="Old Moto").count()
    old_moto_total = old_moto_match_count + old_moto_no_match_count
    old_moto_accuracy = (old_moto_match_count / old_moto_total) * 100 if old_moto_total > 0 else 0

    # New Car
    new_car_match_count = PlateModel.objects.filter(match=True, product="New Car").count()
    new_car_no_match_count = PlateModel.objects.filter(match=False, product="New Car").count()
    new_car_total = new_car_match_count + new_car_no_match_count
    new_car_accuracy = (new_car_match_count / new_car_total) * 100 if new_car_total > 0 else 0

    # Old Car
    old_car_match_count = PlateModel.objects.filter(match=True, product="Old Car").count()
    old_car_no_match_count = PlateModel.objects.filter(match=False, product="Old Car").count()
    old_car_total = old_car_match_count + old_car_no_match_count
    old_car_accuracy = (old_car_match_count / old_car_total) * 100 if old_car_total > 0 else 0

    context = {
        'new_moto_match_count': new_moto_match_count,
        'new_moto_no_match_count': new_moto_no_match_count,
        'new_moto_accuracy': new_moto_accuracy,

        'old_moto_match_count': old_moto_match_count,
        'old_moto_no_match_count': old_moto_no_match_count,
        'old_moto_accuracy': old_moto_accuracy,

        'new_car_match_count': new_car_match_count,
        'new_car_no_match_count': new_car_no_match_count,
        'new_car_accuracy': new_car_accuracy,

        'old_car_match_count': old_car_match_count,
        'old_car_no_match_count': old_car_no_match_count,
        'old_car_accuracy': old_car_accuracy,
    }
    return render(request, 'plate/resultados.html', context)
