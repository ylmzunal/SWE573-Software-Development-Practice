from django.urls import path
from . import views 
from objects import views as object_views
from django.conf import settings
from django.conf.urls.static import static
from .views import vote_comment


urlpatterns = [
    # ... your other URLs ...
    path('vote/comment/<int:comment_id>/<str:vote_type>/', views.vote_comment, name='vote_comment'),
    # ... your other URLs ...
    path('create-post/', views.create_post, name='create_post'),
    path('', views.homepage, name='homepage'),
    path('wikidata-search/', views.wikidata_search, name='wikidata_search'),
    path('accounts/register/', object_views.register, name='register'),
    path('profile/<str:username>/', views.profile_view, name='profile'),
    path('search/', views.search_view, name='search_view'),
    path('search-results/', views.search_view, name='search_results'),
    #path('search-results/<int:post_id>/', views.search_view, name='search_results'),
    path('create-post-form/', views.create_post_form, name='create_post_form'),
    path('post-list-ajax/', views.post_list_ajax, name='post_list_ajax'),
    # path('create-post/', views.create_post_ajax, name='create_post_form'),
    path('create-post/', views.create_post, name='create_post'),
    # path('create-post-ajax/', views.create_post_ajax, name='create_post_ajax'),
    path('post-details/<int:post_id>/', views.post_details, name='post_details'),
    path('add-comment/<int:post_id>/', views.add_comment, name='add_comment'),
    # path('vote/<str:type>/<int:id>/<str:vote_type>/', views.vote, name='vote'),
    path('vote/comment/<int:comment_id>/<str:vote_type>/', views.vote_comment, name='vote_comment'),
    path('post/<int:post_id>/mark-as-solved/', views.mark_as_solved, name='mark_as_solved'),
    path('post/<int:post_id>/', views.post_details, name='post_detail'),
    path('post/<int:post_id>/details/', views.post_details_partial, name='post_details_partial'),
    path('update-bio/', views.update_bio, name='update_bio'),
    # path('post/<int:post_id>/analyze/', views.analyze_post, name='analyze_post'),
    path('post/<int:post_id>/edit/', views.edit_post, name='edit_post'),
    path('post/<int:post_id>/mark-status/', views.mark_post_status, name='mark_post_status'),
    path('edit-comment/<int:comment_id>/', views.edit_comment, name='edit_comment'),
] 

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
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