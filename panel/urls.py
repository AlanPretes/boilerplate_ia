from django.urls import path
from panel import views

app_name = 'panel'

urlpatterns = [
    path('index/', views.index, name='index'),
    path('new/', views.new, name='new'),
    path('resultados/', views.resultados_view, name='resultados'),
    path('api/new-panel/', views.new_plate_api, name='new_panel_api'),
]
