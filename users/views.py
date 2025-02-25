from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth import logout

class CustomLoginView(LoginView):
    template_name = "login.html"  # Substitua pelo nome do seu template de login
    redirect_authenticated_user = True

    def form_invalid(self, form):
        messages.error(self.request, "Usuário ou senha inválidos.", extra_tags="login invalid_login")
        return super().form_invalid(form)

    def get_success_url(self):
        return "/home/"  # Substitua pela URL para onde deseja redirecionar após login bem-sucedido
    
def custom_logout(request):
    logout()
    return redirect('login')
