from django.urls import path
from . import views 
from django.contrib.auth import views as auth_views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('', views.index, name='index'),
    path('my_face_recognition/', views.my_face_recognition, name='face_recognition'),
    path('record/', views.record, name='record'),
    path('add_face/', views.add_face, name='add_face'),
    path('std_record/', views.std_record, name='std_record'),
    path('delete_image/<str:file_name>/', views.delete_image, name='delete_image'),
    path('company/login/', views.company_login, name='company_login'),
    path('employee/login/', views.employee_login, name='employee_login'),
    path('home', views.home, name='home'),
    path('employee/register/', views.employee_register, name='employee_register'),
    path('company/register/', views.company_register, name='company_register'),
    path('company/logout/', views.company_logout, name='company_logout'),


] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
