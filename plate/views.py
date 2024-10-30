from datetime import datetime
from django.shortcuts import render, redirect
from django.urls import reverse
from django.apps import apps  # Para acessar os modelos carregados globalmente
from django.core.files.base import ContentFile
import base64
import requests
import os
from .models import PlateModel
from .utils import PlateRecognitionModel
from django.contrib.auth.decorators import login_required
import tempfile
import zipfile
from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Count, Sum


@login_required
def index(request):
    # Busca todos os registros da tabela PlateModel, ordenando pelo mais recente
    logs = PlateModel.objects.all().order_by('-id')

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
            file_extension = os.path.splitext(file.name)[0]  # Manter a extensão original
            # identifier = file_extension
            # plate = file_extension
            
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

# def download_yolo_txt(request):
#     with tempfile.TemporaryDirectory() as temp_dir:
#         try:
#             unrecognized_dir = os.path.join(temp_dir, 'nao_reconhecido')
#             os.makedirs(unrecognized_dir, exist_ok=True)

#             matched_plates = PlateModel.objects.filter(match=True)
            
#             for plate in matched_plates:
#                 product_dir = os.path.join(temp_dir, plate.product)
#                 images_dir = os.path.join(product_dir, 'images')
#                 labels_dir = os.path.join(product_dir, 'labels')

#                 os.makedirs(images_dir, exist_ok=True)
#                 os.makedirs(labels_dir, exist_ok=True)

#                 # Salvar as imagens top e bottom na pasta images
#                 if plate.img_top:
#                     img_top_path = os.path.join(images_dir, f"{str(plate.img_top).split('/')[-1]}")
#                     with plate.img_top.open("rb") as img_file, open(img_top_path, "wb") as out_file:
#                         out_file.write(img_file.read())

#                 if plate.img_bottom:
#                     img_bottom_path = os.path.join(images_dir, f"{str(plate.img_bottom).split('/')[-1]}")
#                     with plate.img_bottom.open("rb") as img_file, open(img_bottom_path, "wb") as out_file:
#                         out_file.write(img_file.read())

#                 # Gerar e salvar os arquivos txt para top e bottom na pasta labels
#                 try:
#                     if plate.labels_top:
#                         txt_top_content = generate_yolo_txt(plate, 'top')
#                         name = str(plate.img_top).split('/')[-1]
#                         name = name.split(".")[0]
#                         txt_top_filename = f"{name}.txt"
#                         txt_top_filepath = os.path.join(labels_dir, txt_top_filename)
                        
#                         with open(txt_top_filepath, "w") as txt_file:
#                             txt_file.write(txt_top_content)

#                     if plate.labels_bottom:
#                         txt_bottom_content = generate_yolo_txt(plate, 'bottom')
#                         name = str(plate.img_bottom).split('/')[-1]
#                         name = name.split(".")[0]
#                         txt_bottom_filename = f"{name}.txt"
#                         txt_bottom_filepath = os.path.join(labels_dir, txt_bottom_filename)
                        
#                         with open(txt_bottom_filepath, "w") as txt_file:
#                             txt_file.write(txt_bottom_content)
#                 except:
#                     continue

#             unmatched_plates = PlateModel.objects.filter(match=False)
#             for unmatched_plate in unmatched_plates:
#                 # Se o produto não foi reconhecido, salve as imagens na pasta 'nao_reconhecido'
#                 if str(unmatched_plate.product) == 'Produto não reconhecido' or str(unmatched_plate.result) == 'Placa não reconhecida':
#                     unrecognized_image_path = os.path.join(unrecognized_dir, f"{unmatched_plate.identifier}_{unmatched_plate.plate}.jpg")
#                     with unmatched_plate.plate_image.open('rb') as img_file, open(unrecognized_image_path, 'wb') as out_file:
#                         out_file.write(img_file.read())
            
#             # Crie um arquivo .zip contendo as pastas organizadas por tipo de produto
#             zip_filename = "yolo_files.zip"
#             zip_filepath = os.path.join(temp_dir, zip_filename)

#             with zipfile.ZipFile(zip_filepath, 'w') as zip_file:
#                 for root, dirs, files in os.walk(temp_dir):
#                     for file in files:
#                         if file != zip_filename:
#                             arcname = os.path.relpath(os.path.join(root, file), temp_dir)
#                             zip_file.write(os.path.join(root, file), arcname=arcname)

#             # Envie o arquivo .zip como resposta para download
#             with open(zip_filepath, 'rb') as zip_file:
#                 response = HttpResponse(zip_file.read(), content_type='application/zip')
#                 response['Content-Disposition'] = f'attachment; filename={zip_filename}'
#                 return response
#         finally:
#             # Limpar o diretório temporário
#             for root, dirs, files in os.walk(temp_dir, topdown=False):
#                 for name in files:
#                     os.remove(os.path.join(root, name))
#                 for name in dirs:
#                     os.rmdir(os.path.join(root, name))
#             os.rmdir(temp_dir)

@csrf_exempt  # Desativa CSRF para esta view
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
