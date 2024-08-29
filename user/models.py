from django.contrib.auth.models import AbstractUser
from django.db import models
import jwt
from django.conf import settings
from datetime import datetime, timedelta

class CustomUser(AbstractUser):
    jwt_token = models.CharField(max_length=512, blank=True, null=True)

    def save(self, *args, **kwargs):
        # Primeiro salva o usuário para garantir que o ID seja atribuído
        super().save(*args, **kwargs)
        
        # Depois de salvar, gera o token JWT se ainda não existir
        if not self.jwt_token:
            self.jwt_token = self.generate_jwt_token()
            super().save(update_fields=['jwt_token'])

    def generate_jwt_token(self):
        token_data = {
            'id': self.id,  # Certifique-se de que o ID está incluído e é um número
            'username': self.username,
            'exp': datetime.utcnow() + timedelta(days=5)  # ou a duração que preferir
        }
        token = jwt.encode(token_data, settings.SECRET_KEY, algorithm='HS256')
        return token
