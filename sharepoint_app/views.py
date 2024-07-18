from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm
from django.utils import timezone
from .models import Client
from .forms import ClientForm
import msal
import requests
from common.utils import is_token_valid, get_access_token


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                auth_login(request, user)
                return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})


@login_required
def home(request):
    sharepoint_logged_in = 'access_token' in request.session
    return render(request, 'home.html', {'sharepoint_logged_in': sharepoint_logged_in})


@login_required
def login(request):
    user = request.user
    client = Client.objects.get(user=user)
    if is_token_valid(client.token_expires):
        request.session['access_token'] = client.access_token
        return redirect('list_sites')

    tenant_id = "common"  # Use "common" for multi-tenant
    authority = f"https://login.microsoftonline.com/{tenant_id}"
    msal_client = msal.ConfidentialClientApplication(
        client.client_id, authority=authority, client_credential=client.client_secret
    )
    auth_url = msal_client.get_authorization_request_url(
        scopes=["https://graph.microsoft.com/.default"],
        redirect_uri=request.build_absolute_uri('/callback/'),
    )
    return redirect(auth_url)


@login_required
def callback(request):
    code = request.GET.get('code')
    user = request.user
    client = Client.objects.get(user=user)
    tenant_id = "common"
    authority = f"https://login.microsoftonline.com/{tenant_id}"
    msal_client = msal.ConfidentialClientApplication(
        client.client_id, authority=authority, client_credential=client.client_secret
    )
    result = msal_client.acquire_token_by_authorization_code(
        code,
        scopes=["https://graph.microsoft.com/.default"],
        redirect_uri=request.build_absolute_uri('/callback/'),
    )
    if "access_token" in result:
        client.access_token = result["access_token"]
        client.refresh_token = result.get("refresh_token")
        client.token_expires = timezone.now() + timezone.timedelta(seconds=result["expires_in"])
        client.save()
        request.session["access_token"] = result["access_token"]
        return redirect('list_sites')
    else:
        return render(request, 'error.html', {"error": result.get("error")})


@login_required
def list_sites(request):
    try:
        access_token = get_access_token(request.user)
    except Exception as e:
        return redirect('login')

    request.session['access_token'] = access_token
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json',
    }
    response = requests.get(
        "https://graph.microsoft.com/v1.0/sites?search=*",
        headers=headers
    )
    if response.status_code == 401:  # Token is invalid or expired
        return redirect('login')

    sites = response.json().get('value', [])
    return render(request, 'sites.html', {'sites': sites})


@login_required
def list_document_libraries(request, site_id):
    access_token = get_access_token(request.user)
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json',
    }
    response = requests.get(
        f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives",
        headers=headers
    )
    libraries = response.json().get('value', [])
    return render(request, 'libraries.html', {'libraries': libraries, 'site_id': site_id})


@login_required
def list_items_in_library(request, site_id, library_id, folder_id='root'):
    access_token = get_access_token(request.user)
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json',
    }
    response = requests.get(
        f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{library_id}/items/{folder_id}/children",
        headers=headers
    )
    items = response.json().get('value', [])
    return render(request, 'items.html', {'items': items, 'site_id': site_id, 'library_id': library_id})


@login_required
def download_file(request, site_id, library_id, item_id):
    access_token = get_access_token(request.user)
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json',
    }
    response = requests.get(
        f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{library_id}/items/{item_id}",
        headers=headers
    )
    file = response.json()
    file_url = file['@microsoft.graph.downloadUrl']
    return redirect(file_url)


def register_client(request):
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save(commit(False))
            client.user = request.user
            client.save()
            return redirect('login_view')
    else:
        form = ClientForm()
    return render(request, 'register_client.html', {'form': form})
