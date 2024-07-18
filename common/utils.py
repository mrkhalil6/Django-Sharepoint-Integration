from datetime import datetime

import msal
from django.utils import timezone

from sharepoint_app.models import Client


def is_token_valid(token_expires):
    return token_expires and token_expires > timezone.now()


def get_access_token(user):
    client = Client.objects.get(user=user)
    if is_token_valid(client.token_expires):
        return client.access_token

    tenant_id = "common"
    authority = f"https://login.microsoftonline.com/{tenant_id}"
    msal_client = msal.ConfidentialClientApplication(
        client.client_id, authority=authority, client_credential=client.client_secret
    )
    result = msal_client.acquire_token_by_refresh_token(
        client.refresh_token, scopes=["https://graph.microsoft.com/.default"]
    )
    if "access_token" in result:
        client.access_token = result["access_token"]
        client.refresh_token = result.get("refresh_token")
        client.token_expires = timezone.now() + timezone.timedelta(seconds=result["expires_in"])
        client.save()
        return client.access_token
    else:
        raise Exception("Could not refresh token")
