from django.urls import path, include
from . import views

urlpatterns = [
    path("", views.signup, name='signup'),
    path(r'signup/', views.signup, name='signup'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('scrape/', views.scrape, name='scrape'),
    path('scrape/get_locations', views.get_locations, name='get_locations'),
    path('grocery_lists/', views.grocery_lists),
]
