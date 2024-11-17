from django.urls import path
from . import views
from objects import views as object_views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('wikidata-search/', views.search_view, name='wikidata_search'),
    path('accounts/register/', object_views.register, name='register'),
    path('profile/<str:username>/', views.profile_view, name='profile'),
    path('search/', views.search_view, name='search_view'),
    path('search-results/', views.search_view, name='search_results'),
    path('create-post-form/', views.create_post_form, name='create_post_form'),
    path('post-list-ajax/', views.post_list_ajax, name='post_list_ajax'),
    path('post-details/<int:post_id>/', views.post_details, name='post_details'),
    path('add-comment/<int:post_id>/', views.add_comment, name='add_comment'),
    path('vote/<str:type>/<int:id>/<str:vote_type>/', views.vote, name='vote'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# urlpatterns = [
#     path('', views.homepage, name='homepage'),
#     path('accounts/register/', object_views.register, name='register'),
#     path('search/', views.search_results, name='search_results'),
#     path('accounts/register/', views.register, name='register'),
#     path('register/', views.register, name='register'),
#     path('profile/<str:username>/', views.profile_view, name='profile'), 
#     path('search/', views.search_results, name='search_results'),
#     path('create-post-form/', views.create_post_form, name='create_post_form'),
#     # path('create-post-ajax/', views.create_post_ajax, name='create_post_ajax'),
#     path('post-list-ajax/', views.post_list_ajax, name='post_list_ajax'),
#     path('post-details/<int:post_id>/', views.post_details, name='post_details'),
#     path('add-comment/<int:post_id>/', views.add_comment, name='add_comment'),
#     path('vote/<str:type>/<int:id>/<str:vote_type>/', views.vote, name='vote'),
# ]

# if settings.DEBUG:
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


