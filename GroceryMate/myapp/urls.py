from django.urls import path, include

from . import views

urlpatterns = [
    path("", views.signup, name='signup'),
    path(r'signup/', views.signup, name='signup'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('logout_user/', views.logout_user, name='logout'),
    path('accounts/edit-profile/',views.edit_user_profile, name='edit_user_profile'),
    path('scrape/', views.scrape, name='scrape'),
    path('scrape/get_locations', views.scrape, name='get_locations'),
    path('scrape/get_products_prices', views.scrape, name='get_products_prices'),
    path('grocery_lists/', views.grocery_lists, name = 'grocery_lists'),
    path('save_grocery_lists/', views.save_grocery_lists),
    path('delete_grocery_list/<int:id>', views.delete_grocery_list),
    path('edit_grocery_list/<int:id>', views.edit_grocery_list),
    path('grocery_items/<int:id>', views.grocery_items),
    path('get_products/', views.get_products),
    path('get_prices/', views.get_prices),
    path('add_grocery_list_item/', views.add_grocery_list_item),
    path('delete_grocery_list_item/<int:id>', views.delete_grocery_list_item),
    path('get_nutrition_info/<str:name>', views.get_nutrition_info)
]
