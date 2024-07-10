# sharepoint_app/forms.py
from django import forms
from .models import Client


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['tenant_id', 'client_id', 'client_secret']
