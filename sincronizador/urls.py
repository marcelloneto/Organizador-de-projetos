from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/read-properties/', views.read_properties, name='read_properties'),
    path('api/write-properties/', views.write_properties, name='write_properties'),
]