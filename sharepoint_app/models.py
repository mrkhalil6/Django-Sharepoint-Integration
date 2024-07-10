# sharepoint_app/models.py
from django.db import models
from django.contrib.auth.models import User

class Client(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    tenant_id = models.CharField(max_length=100)
    client_id = models.CharField(max_length=100)
    client_secret = models.CharField(max_length=100)
    access_token = models.TextField(null=True, blank=True)
    refresh_token = models.TextField(null=True, blank=True)
    token_expires = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.user.username
