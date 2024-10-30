from django.urls import path
from . import views

app_name = 'plate'

urlpatterns = [
    path('index/', views.index, name='index'),  # Rota para a página inicial
    path('new/', views.new, name='new'),  # Rota para criar uma nova consulta
    path('resultados/', views.resultados_view, name='resultados'),
    path('api/new-plate/', views.new_plate_api, name='new_plate_api'),
    # path('download-yolo-txt/', views.download_yolo_txt, name='download_yolo_txt'),
]
