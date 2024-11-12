from django.urls import path
from . import views
from objects import views as object_views

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('accounts/register/', object_views.register, name='register'),
    path('search/', views.search_results, name='search_results'),  # Make sure this line has a comma at the end
    path('comment/<int:post_id>/', views.add_comment, name='add_comment'),  # Add other paths as needed
    path('accounts/register/', views.register, name='register'),
    path('register/', views.register, name='register'),
    path('profile/<str:username>/', views.profile_view, name='profile'), 
    path('search/', views.search_view, name='search'),
]