from django.urls import path, include
from . import views

urlpatterns = [
    path("", views.signup, name='signup'),
    path(r'signup/', views.signup, name='signup'),
    path('accounts/', include('django.contrib.auth.urls')),
]
