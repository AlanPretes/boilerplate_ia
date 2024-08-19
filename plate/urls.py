from django.urls import path
from . import views

app_name = 'plate'

urlpatterns = [
    path('index/', views.index, name='index'),  # Rota para a página inicial
    path('new/', views.new, name='new'),  # Rota para criar uma nova consulta
    path('download-yolo-txt/', views.download_yolo_txt, name='download_yolo_txt'),
]