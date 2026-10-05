from django.shortcuts import redirect
from django.urls import reverse

class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Defina aqui as rotas que NÃO precisam de login (como a própria tela de login e o admin, se necessário)
        rotas_isentas = [reverse('login'), '/admin/']
        
        # Verifica se o usuário não está autenticado e a rota atual não está na lista de isentas
        if not request.user.is_authenticated:
            if not any(request.path.startswith(rota) for rota in rotas_isentas):
                return redirect('login')

        response = self.get_response(request)
        return response