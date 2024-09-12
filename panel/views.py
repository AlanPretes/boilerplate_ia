from datetime import datetime
from django.shortcuts import render, redirect
from django.urls import reverse
from django.apps import apps  # Para acessar os modelos carregados globalmente
from django.core.files.base import ContentFile
import base64
import requests
import os
from .models import PanelModel
from .utils import PanelAlerts
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
from PIL import Image
from io import BytesIO
from urllib.parse import urlparse


@login_required
def index(request):
    # Busca todos os registros da tabela PlateModel, ordenando pelo mais recente
    logs = PanelModel.objects.all().order_by('-id')

    context = {
        'logs': logs,
    }

    return render(request, 'panel/index.html', context)

@login_required
def new(request):
    if request.method == 'POST':
        start = datetime.now()
        identifier = request.POST.get('identifier')
        files = request.FILES.getlist('file')  # Obter todos os arquivos
        thumbs = request.POST.get('thumbs') == 'true'
        

        for file in files:
            file_extension = os.path.splitext(file.name)[0]  # Manter a extensão original
            # identifier = file_extension
            # plate = file_extension
            
            new_panel = PanelModel(
                identifier=str(identifier),
                runtime=0.0
            )

            new_panel.image_airbag_icon_origin = file
            new_panel.save()

            image_path_origin = new_panel.image_airbag_icon_origin.path
            image_name = str(new_panel.image_airbag_icon_origin.name).split("/")[-1]
            print(image_name)

            app_config = apps.get_app_config('panel')
            model_airbag_icon = app_config.model_airbag_icon
            panel_recognition_model = PanelAlerts(model_airbag_icon)

            # Faz a predição usando o caminho da imagem salva
            result = panel_recognition_model.predict(image_path_origin, image_name=image_name)
            
            # Extrai o thumb do resultado
            thumb = result.get('thumb')

            if thumbs and thumb and thumb != "Erro ao criar thumb":       
                new_panel.image_airbag_icon = thumb
            else:
                # Caso contrário, usa o arquivo original (path)
                new_panel.image_airbag_icon = file
                 
            # Associa o resultado ao modelo PlateModel
            new_panel.airbag_icon = result.get('airbag_icon')

            new_panel.runtime = (datetime.now() - start).total_seconds()
            new_panel.save()

        return redirect(reverse('panel:index'))
    
    return render(request, 'panel/new.html')


# def generate_yolo_txt(plate_model, label_type):
#     """
#     Gera o conteúdo do arquivo .txt no formato YOLO com base nas coordenadas.
#     `label_type` deve ser 'top' ou 'bottom' para gerar o arquivo correspondente.
#     """
#     lines = []
#     labels = plate_model.labels_top if label_type == 'top' else plate_model.labels_bottom

#     for label in labels:
#         class_id, x_center, y_center, width, height = label
#         lines.append(f"{class_id} {x_center} {y_center} {width} {height}")

#     return "\n".join(lines)

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
    start = datetime.now()
    identifier = request.data.get('identifier')
    image_url = request.data.get('image_url')  # Obter todos os arquivos
    thumbs = request.data.get('thumbs')
    
    if not image_url:
        return Response({'error': 'Image URL is required.'}, status=status.HTTP_400_BAD_REQUEST)

    # Baixar a imagem da URL
    response = requests.get(image_url)
    if response.status_code != 200:
        return Response({'error': 'Failed to download image.'}, status=status.HTTP_400_BAD_REQUEST)
    
    parsed_url = urlparse(image_url)
    image_name = parsed_url.path.split('/')[-1]
    image_file = ContentFile(response.content, name=image_name)
    
    new_panel = PanelModel(
        identifier=str(identifier),
        runtime=0.0
    )

    new_panel.image_airbag_icon_origin = image_file
    new_panel.save()

    image_path_origin = new_panel.image_airbag_icon_origin.path
    image_name = str(new_panel.image_airbag_icon_origin.name).split("/")[-1]

    app_config = apps.get_app_config('panel')
    model_airbag_icon = app_config.model_airbag_icon
    panel_recognition_model = PanelAlerts(model_airbag_icon)

    # Faz a predição usando o caminho da imagem salva
    result = panel_recognition_model.predict(image_path_origin, image_name=image_name)
    print(result)
    
    # Extrai o thumb do resultado
    thumb = result.get('thumb')

    if thumbs and thumb and thumb != "Erro ao criar thumb":       
        new_panel.image_airbag_icon = thumb
    else:
        # Caso contrário, usa o arquivo original (path)
        new_panel.image_airbag_icon = image_file
            
    # Associa o resultado ao modelo PlateModel
    new_panel.airbag_icon = result.get('airbag_icon')

    new_panel.runtime = (datetime.now() - start).total_seconds()
    new_panel.save()
    
   

    response_data = {
        "identificador": identifier,
        "result": new_panel.airbag_icon,
        "runtime": new_panel.runtime
    }

    return Response(response_data, status=status.HTTP_201_CREATED)


@login_required
def resultados_view(request):
    airbag_icon_count = PanelModel.objects.filter(airbag_icon="Ícone AirBag detectado").count()

    context = {
        'airbag_icon_count': airbag_icon_count,
    }
    return render(request, 'panel/resultados.html', context)
