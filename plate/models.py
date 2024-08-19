from django.db import models
import os

def upload_to_plate(instance, filename):
    # Extrai a extensão do arquivo
    ext = filename.split('.')[-1]
    # Define o nome do arquivo como o valor de 'identifier' com a extensão original
    filename = f"{instance.identifier}.{ext}"
    # Retorna o caminho completo onde o arquivo será salvo
    return os.path.join('images/plates/', filename)

def upload_to_img_top(instance, filename):
    # Extrai a extensão do arquivo
    ext = filename.split('.')[-1]
    # Define o nome do arquivo como "identifier_top" com a extensão original
    filename = f"{instance.identifier}_top.{ext}"
    # Retorna o caminho completo onde o arquivo será salvo
    return os.path.join('images/plates/top/', filename)

def upload_to_img_bottom(instance, filename):
    # Extrai a extensão do arquivo
    ext = filename.split('.')[-1]
    # Define o nome do arquivo como "identifier_bottom" com a extensão original
    filename = f"{instance.identifier}_bottom.{ext}"
    # Retorna o caminho completo onde o arquivo será salvo
    return os.path.join('images/plates/bottom/', filename)

class PlateModel(models.Model):
    identifier = models.CharField(max_length=255, null=False)
    product = models.CharField(max_length=255, null=False)
    plate = models.CharField(max_length=255, null=False)
    result = models.JSONField(null=True, blank=True)
    labels_top = models.JSONField(null=True, blank=True)
    labels_bottom = models.JSONField(null=True, blank=True)
    img_top = models.ImageField(upload_to=upload_to_img_top, null=True, blank=True)  # Usando a função 'upload_to_img_top'
    img_bottom = models.ImageField(upload_to=upload_to_img_bottom, null=True, blank=True)  # Usando a função 'upload_to_img_bottom'
    match = models.BooleanField(default=False)
    runtime = models.FloatField(default=0.0)
    plate_image = models.ImageField(upload_to=upload_to_plate, null=True, blank=True)  # Usando a função 'upload_to_plate'

    def __str__(self):
        return f'Log {self.identifier} for product {self.product}'