from datetime import datetime
from django.shortcuts import render, redirect
from django.urls import reverse
from django.apps import apps  # Para acessar os modelos carregados globalmente
from django.core.files.base import ContentFile
import base64
import os
from .models import PlateModel
from .utils import PlateRecognitionModel
from django.contrib.auth.decorators import login_required
import tempfile
import zipfile
from django.http import HttpResponse

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
        # identifier = request.POST.get('identifier')
        # plate = str(request.POST.get('plate')).upper()
        files = request.FILES.getlist('file')  # Obter todos os arquivos
        thumbs = request.POST.get('thumbs') == 'true'
        

        for file in files:
            file_extension = os.path.splitext(file.name)[0]  # Manter a extensão original
            identifier = file_extension
            plate = file_extension
            
            new_plate = PlateModel(
                identifier=str(file_extension),
                plate=str(file_extension),
                product="",
                runtime=0.0
            )

            new_plate.plate_image = file
            new_plate.save()

            image_path = new_plate.plate_image.path

            app_config = apps.get_app_config('plate')
            model_crop = app_config.model_crop
            model_letters = app_config.model_letters
            plate_recognition_model = PlateRecognitionModel(model_crop, model_letters)

            # Faz a predição usando o caminho da imagem salva
            result = plate_recognition_model.predict(image_path, thumbs=thumbs)

            if result.get('product') == 'Produto não reconhecido' or result.get('result') == 'Placa não reconhecida':
                # Determina o caminho de salvamento na pasta 'nao_reconhecido'
                save_directory = 'nao_reconhecido/'
                os.makedirs(save_directory, exist_ok=True)  # Cria o diretório se não existir

                # Reabre o arquivo para leitura e salva na pasta 'nao_reconhecido'
                file.seek(0)  # Garante que o ponteiro do arquivo esteja no início
                unrecognized_image_name = os.path.join(save_directory, f"{identifier}_{file.name}")
                with open(unrecognized_image_name, 'wb') as f:
                    f.write(file.read())

            # Salva as imagens `thumb_top` e `thumb_bottom`
            if result.get('thumb_top'):
                save_directory = './media/images/plates/top'
                thumb_top_data = base64.b64decode(result['thumb_top'])
                thumb_top_name = os.path.join(save_directory, f"{identifier}_{file.name}_top.jpg")
                new_plate.img_top.save(thumb_top_name, ContentFile(thumb_top_data))

            if result.get('thumb_bottom'):
                save_directory = './media/images/plates/bottom'
                thumb_bottom_data = base64.b64decode(result['thumb_bottom'])
                thumb_bottom_name = os.path.join(save_directory, f"{identifier}_{file.name}_bottom.jpg")
                new_plate.img_bottom.save(thumb_bottom_name, ContentFile(thumb_bottom_data))

            # Associa o resultado ao modelo PlateModel
            new_plate.product = result.get('product', 'Produto Desconhecido')
            new_plate.labels_top = result.get('labels_top', [])
            new_plate.labels_bottom = result.get('labels_bottom', [])
            new_plate.result = result.get('result', 'Placa não reconhecida')

            if result['result'] == plate:
                new_plate.match = True

            new_plate.runtime = (datetime.now() - start).total_seconds()
            new_plate.save()

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

def download_yolo_txt(request):
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            unrecognized_dir = os.path.join(temp_dir, 'nao_reconhecido')
            os.makedirs(unrecognized_dir, exist_ok=True)

            matched_plates = PlateModel.objects.filter(match=True)
            
            for plate in matched_plates:
                product_dir = os.path.join(temp_dir, plate.product)
                images_dir = os.path.join(product_dir, 'images')
                labels_dir = os.path.join(product_dir, 'labels')

                os.makedirs(images_dir, exist_ok=True)
                os.makedirs(labels_dir, exist_ok=True)

                # Salvar as imagens top e bottom na pasta images
                if plate.img_top:
                    img_top_path = os.path.join(images_dir, f"{plate.identifier}_top.jpg")
                    with plate.img_top.open("rb") as img_file, open(img_top_path, "wb") as out_file:
                        out_file.write(img_file.read())

                if plate.img_bottom:
                    img_bottom_path = os.path.join(images_dir, f"{plate.identifier}_bottom.jpg")
                    with plate.img_bottom.open("rb") as img_file, open(img_bottom_path, "wb") as out_file:
                        out_file.write(img_file.read())

                # Gerar e salvar os arquivos txt para top e bottom na pasta labels
                try:
                    if plate.labels_top:
                        txt_top_content = generate_yolo_txt(plate, 'top')
                        txt_top_filename = f"{plate.identifier}_top.txt"
                        txt_top_filepath = os.path.join(labels_dir, txt_top_filename)
                        
                        with open(txt_top_filepath, "w") as txt_file:
                            txt_file.write(txt_top_content)

                    if plate.labels_bottom:
                        txt_bottom_content = generate_yolo_txt(plate, 'bottom')
                        txt_bottom_filename = f"{plate.identifier}_bottom.txt"
                        txt_bottom_filepath = os.path.join(labels_dir, txt_bottom_filename)
                        
                        with open(txt_bottom_filepath, "w") as txt_file:
                            txt_file.write(txt_bottom_content)
                except:
                    continue

                # Se o produto não foi reconhecido, salve as imagens na pasta 'nao_reconhecido'
                if plate.product == 'Produto não reconhecido' or plate.result == 'Placa não reconhecida':
                    unrecognized_image_path = os.path.join(unrecognized_dir, f"{plate.identifier}.jpg")
                    with plate.plate_image.open('rb') as img_file, open(unrecognized_image_path, 'wb') as out_file:
                        out_file.write(img_file.read())
            
            # Crie um arquivo .zip contendo as pastas organizadas por tipo de produto
            zip_filename = "yolo_files.zip"
            zip_filepath = os.path.join(temp_dir, zip_filename)

            with zipfile.ZipFile(zip_filepath, 'w') as zip_file:
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        if file != zip_filename:
                            arcname = os.path.relpath(os.path.join(root, file), temp_dir)
                            zip_file.write(os.path.join(root, file), arcname=arcname)

            # Envie o arquivo .zip como resposta para download
            with open(zip_filepath, 'rb') as zip_file:
                response = HttpResponse(zip_file.read(), content_type='application/zip')
                response['Content-Disposition'] = f'attachment; filename={zip_filename}'
                return response
        finally:
            # Limpar o diretório temporário
            for root, dirs, files in os.walk(temp_dir, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(temp_dir)
