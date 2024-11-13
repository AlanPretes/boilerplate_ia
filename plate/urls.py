from django.urls import path
from . import views

app_name = 'plate'

urlpatterns = [
    path('index/', views.index, name='index'), 
    path('new/', views.new, name='new'), 
    path('resultados/', views.resultados_view, name='resultados'),
    path('api/new-plate/', views.new_plate_api, name='new_plate_api'),
]
