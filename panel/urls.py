from django.urls import path
from . import views

app_name = 'panel'

urlpatterns = [
    path('index/', views.index, name='index'),
    path('new/', views.new, name='new'),
    # path('resultados/', views.resultados_view, name='resultados'),
    # path('api/new-panel/', views.new_plate_api, name='new_panel_api'),
    # path('download-yolo-txt/', views.download_yolo_txt, name='download_yolo_txt'),
]
