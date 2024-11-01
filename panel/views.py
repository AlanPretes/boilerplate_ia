import os
from datetime import datetime

import requests
from django.shortcuts import render, redirect
from django.urls import reverse
from django.apps import apps
from django.core.files.base import ContentFile
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from urllib.parse import urlparse

from panel.models import PanelModel
from panel.utils import PanelAlerts

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status


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
            new_panel = PanelModel(
                identifier=str(identifier),
                runtime=0.0
            )

            new_panel.image_airbag_icon_origin = file
            new_panel.save()

            image_path_origin = new_panel.image_airbag_icon_origin.path
            image_name = str(new_panel.image_airbag_icon_origin.name).split("/")[-1]

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
