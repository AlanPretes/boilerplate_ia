from django.contrib.auth.views import LoginView
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import CustomUser
import uuid

class CustomLoginView(LoginView):
    template_name = 'login.html'  # Substitua pelo caminho do seu template de login

@receiver(post_save, sender=CustomUser)
def create_user_token(sender, instance=None, created=False, **kwargs):
    if created:
        instance.api_token = str(uuid.uuid4().hex)  # Ou algum outro método de geração de token fixo
        instance.save()