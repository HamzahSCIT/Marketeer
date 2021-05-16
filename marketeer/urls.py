from django.contrib import admin
from django.urls import path, include
from django.conf.urls import url

from accounts import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    url('generate_description/', views.generate_description, name='generate_description'),
    url('save_description/', views.save_description, name="save_description"),
    path('prod_list/', views.product_list, name="pro_list"),
    path('signup/', views.signup, name='signup'),
    path('deleteDescription/<int:product_id>/', views.deleteDescription, name="deleteDescription"),
    url('translate/', views.translate, name="translate"),
]
