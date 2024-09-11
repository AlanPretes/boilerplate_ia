from django.db import models
import os

def upload_to_plate(instance, filename):
    # Extrai a extensão do arquivo
    ext = filename.split('.')[-1]
    # Define o nome do arquivo como o valor de 'identifier' com a extensão original
    filename = f"{instance.identifier}.{ext}"
    # Retorna o caminho completo onde o arquivo será salvo
    return os.path.join('images/plates/complete', filename)

class PanelModel(models.Model):
    identifier = models.CharField(max_length=255, null=False)
    airbag_icon = models.JSONField(null=True, blank=True)
    labels = models.JSONField(null=True, blank=True)
    image_airbag_icon_origin = models.ImageField(upload_to='./images/panel/complete', max_length=255, null=True, blank=True)
    image_airbag_icon = models.ImageField(upload_to='./images/panel/reconhecidas_airbag', max_length=255, null=True, blank=True)
    runtime = models.FloatField(default=0.0)

    def __str__(self):
        return f'Log {self.identifier} for product {self.product}'
