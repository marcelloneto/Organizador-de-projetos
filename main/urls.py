from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.lista_os_view, name='lista_os'),
    path('os/<int:os_id>/', views.detalhe_os_view, name='detalhe_os'),
    path('os/nova/', views.cadastrar_os, name='cadastrar_os'),
    path('os/<int:os_id>/editar/', views.editar_os, name='editar_os'),
    path('os/<int:os_id>/excluir/', views.excluir_os, name='excluir_os'),
    
    # Conjunto
    path('os/<int:os_id>/conjunto/novo/', views.cadastrar_conjunto, name='cadastrar_conjunto'),
    path('conjunto/<int:pk>/editar/', views.editar_conjunto, name='editar_conjunto'),
    path('conjunto/<int:pk>/excluir/', views.excluir_conjunto, name='excluir_conjunto'),

    # Subconjunto
    path('conjunto/<int:conjunto_id>/subconjunto/novo/', views.cadastrar_subconjunto, name='cadastrar_subconjunto'),
    path('subconjunto/<int:pk>/editar/', views.editar_subconjunto, name='editar_subconjunto'),
    path('subconjunto/<int:pk>/excluir/', views.excluir_subconjunto, name='excluir_subconjunto'),

    # Item
    path('subconjunto/<int:subconjunto_id>/item/novo/', views.cadastrar_item, name='cadastrar_item'),
    path('item/<int:pk>/editar/', views.editar_item, name='editar_item'),
    path('item/<int:pk>/excluir/', views.excluir_item, name='excluir_item'),

    # Documento (Informações básicas / Hierarquia)
    path('item/<int:item_id>/documento/novo/', views.cadastrar_documento, name='cadastrar_documento'),
    path('documento/<int:pk>/editar/', views.editar_documento, name='editar_documento'),
    path('documento/<int:pk>/excluir/', views.excluir_documento, name='excluir_documento'),

    # Janela Separada para Status, Caminhos e Revisão
    path('documento/<int:pk>/gerenciar/', views.gerenciar_documento_arquivos, name='gerenciar_documento_arquivos'),

    path('documento/<int:pk>/visualizar-pdf/', views.visualizar_pdf, name='visualizar_pdf'),
    path('documento/<int:pk>/baixar/<str:tipo>/', views.baixar_arquivo, name='baixar_arquivo'),

    path('login/', auth_views.LoginView.as_view(template_name='main/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]