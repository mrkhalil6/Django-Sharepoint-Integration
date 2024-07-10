from django.contrib import admin
from django.urls import path
from sharepoint_app import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/login/', views.login_view, name='login_view'),
    path('login/', views.login, name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('', views.home, name='home'),
    path('callback/', views.callback, name='callback'),
    path('sites/', views.list_sites, name='list_sites'),
    path('sites/<str:site_id>/libraries/', views.list_document_libraries, name='list_document_libraries'),
    path('sites/<str:site_id>/libraries/<str:library_id>/items/', views.list_items_in_library, name='list_items_in_library'),
    path('sites/<str:site_id>/libraries/<str:library_id>/items/<str:folder_id>/', views.list_items_in_library, name='list_items_in_folder'),
    path('sites/<str:site_id>/libraries/<str:library_id>/items/<str:item_id>/download/', views.download_file, name='download_file'),
]