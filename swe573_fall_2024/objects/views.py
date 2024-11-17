import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from .models import Post, Comment
from .forms import PostForm, CommentForm
from django.contrib.auth import login, authenticate
from .forms import RegistrationForm, RegisterForm
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from PIL import Image



def homepage(request):
    # Handle new post submission
    if request.method == 'POST':
        post_form = PostForm(request.POST)
        if post_form.is_valid():
            post_form.save()
            return redirect('homepage')
    else:
        post_form = PostForm()

    # Fetch all posts with related comments
    posts = Post.objects.annotate(comment_count=Count('comments')).all().order_by('-created_at')
    context = {
        'post_form': post_form,
        'posts': posts
    }
    return render(request, 'homepage.html', context)

def search_view(request):
    query = request.GET.get('q')  # Get the search term from the query parameters
    category = request.GET.get('category')  # Optional: Get category if you want to filter by category
    wikidata_results = []  # Initialize an empty list for results

    if query:  # Check if a search query was provided
        # Perform the search query on the model fields
        wikidata_results = Post.objects.filter(
            Q(title__icontains=query) | Q(content__icontains=query)
        )
        # If category filtering is needed, add it to the filter query
        if category:
            wikidata_results = wikidata_results.filter(category__icontains=category)

    context = {
        'wikidata_results': wikidata_results,
        'query': query,  # Pass the query to the template for display or debugging
    }
    return render(request, 'search_results.html', context)

def search_results(request):
    query = request.GET.get('q', '').strip()
    wikidata_results = Post.objects.filter(
        Q(title__icontains=query) | Q(content__icontains=query)
    ) if query else None

    context = {
        'wikidata_results': wikidata_results,
        'query': query
    }
    return render(request, 'search_results.html', context)

# Dummy function to represent search logic - replace this with your actual logic

def search_wikidata(query, category):
    # Example of querying the Wikidata API
    url = "https://www.wikidata.org/w/api.php"
    params = {
        'action': 'wbsearchentities',
        'format': 'json',
        'language': 'en',
        'search': query
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        results = [
            {
                'label': item.get('label'),
                'description': item.get('description')
            }
            for item in data.get('search', [])
        ]
        return results
    return []

@login_required
def profile_view(request, username):
    user = get_object_or_404(User, username=username)

    # Fetch user-related data
    posts = Post.objects.filter(user=user)
    comments = Comment.objects.filter(user=user)

    context = {
        'user_profile': user,
        'bio': user.profile.bio if hasattr(user, 'profile') else 'No bio available.',
        'total_posts': posts.count(),
        'total_comments': comments.count(),
        'upvotes': sum(post.upvotes for post in posts),  # Assuming 'upvotes' is a field in Post
        'downvotes': sum(post.downvotes for post in posts),  # Assuming 'downvotes' is a field in Post
        'badges': user.profile.badges if hasattr(user, 'profile') and user.profile.badges else ['No badges yet.'],
        'achievements': user.profile.achievements if hasattr(user, 'profile') and user.profile.achievements else ['No achievements yet.'],
        'posts': posts,
    }
    return render(request, 'profile.html', context)


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('homepage')  # Kayıt sonrası ana sayfaya yönlendir
    else:
        form = RegisterForm()
    return render(request, 'registration/register.html', {'form': form})

# Profile view
def profile(request, user_id):
    user = get_object_or_404(User, id=user_id)
    return render(request, 'profile.html', {'profile_user': user})

@login_required
def create_post_form(request):
    form = PostForm()
    return render(request, 'post_form.html', {'form': form})


@login_required
def create_post_ajax(request):
    """
    AJAX ile Post oluşturma görünümü. 
    Kullanıcıdan gelen POST ve FILES verilerini alır, PostForm'u doğrular ve kaydeder.
    """
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)  # Hem POST hem de dosyaları al
        if form.is_valid():
            # Mevcut kullanıcının postu olduğunu belirt
            post = form.save(commit=False)
            post.author = request.user  # Kullanıcıyı ilişkilendir
            
            # Resmi silme kontrolü
            if form.cleaned_data.get('delete_image'):
                if post.image:  # Mevcut bir resim varsa
                    post.image.delete(save=False)  # Resmi sil
                post.image = None

            # Post'u kaydet
            post.save()

            # Resim boyutlandırma işlemi
            if post.image:
                try:
                    img = Image.open(post.image.path)
                    max_size = (800, 800)  # Standart boyut
                    img.thumbnail(max_size, Image.ANTIALIAS)
                    img.save(post.image.path)  # Yeniden boyutlandırılmış resmi kaydet
                except Exception as e:
                    return JsonResponse({
                        'success': False,
                        'message': f'Resim işleme hatası: {str(e)}',
                    })

            # Başarılı yanıt döndür
            return JsonResponse({
                'success': True,
                'message': 'Post başarıyla oluşturuldu.',
                'post': {
                    'id': post.id,
                    'title': post.title,
                    'content': post.content,
                    'image_url': post.image.url if post.image else None,  # Resim URL'si
                }
            })
        else:
            # Hata durumunda, formdaki hataları JSON olarak döndür
            return JsonResponse({
                'success': False,
                'errors': form.errors.as_json(),
            })

    # POST dışındaki metodlar için hata yanıtı
    return JsonResponse({
        'success': False,
        'message': 'Yalnızca POST metodu desteklenmektedir.',
    }, status=400)


def post_list_ajax(request):
    posts = Post.objects.all()
    return render(request, 'post_list.html', {'posts': posts})

def post_details(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    return render(request, 'post_details.html', {'post': post})

# def add_comment(request, post_id):
#     if request.method == 'POST' and request.is_ajax():
#         post = get_object_or_404(Post, id=post_id)
#         content = request.POST.get('content', '').strip()
#         if content:
#             Comment.objects.create(
#                 post=post,
#                 user=request.user if request.user.is_authenticated else None,
#                 content=content
#             )
#             # Dinamik olarak güncellenmiş yorumları döndür
#             return render(request, 'partials/comments_list.html', {'comments': post.comments.all()})
#         return JsonResponse({'error': 'Comment content cannot be empty.'}, status=400)
#     return JsonResponse({'error': 'Invalid request'}, status=400)

# def add_comment(request, post_id):
#     if request.method == 'POST':
#         post = get_object_or_404(Post, id=post_id)
#         content = request.POST.get('content', '').strip()
#         if content:
#             comment = Comment.objects.create(
#                 post=post,
#                 user=request.user if request.user.is_authenticated else None,
#                 content=content
#             )
#             # Yorum bilgilerini döndürün
#             return JsonResponse({
#                 'success': True,
#                 'comment': {
#                     'content': comment.content,
#                     'username': comment.user.username if comment.user else "Anonymous",
#                     'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
#                 }
#             })
#         return JsonResponse({'success': False, 'error': 'Comment content cannot be empty.'}, status=400)
#     return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=400)


# def add_comment(request, post_id):
#     if request.method == 'POST':
#         post = Post.objects.get(id=post_id)
#         text = request.POST.get('comment')
#         Comment.objects.create(post=post, user=request.user if request.user.is_authenticated else None, text=text)
#         return HttpResponseRedirect(reverse('post_details', args=[post_id]))


# def post_details(request, post_id):
#     post = get_object_or_404(Post, id=post_id)
#     comments = post.comments.all().order_by('-created_at')  # Yorumları sıralayın
#     context = {
#         'post': post,
#         'comments': comments,
#     }
#     return render(request, 'post_details.html', context)

def add_comment(request, post_id):
    if request.method == 'POST':
        post = get_object_or_404(Post, id=post_id)
        content = request.POST.get('content', '').strip()
        if content:
            # Yorum kaydet
            Comment.objects.create(
                post=post,
                user=request.user if request.user.is_authenticated else None,
                content=content
            )
            # Yorum eklendikten sonra ilgili gönderiye yönlendir
            return redirect('homepage')
        else:
            # İçerik boşsa hata mesajı göster
            return redirect('homepage')

    return redirect('homepage')

def post_details(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.all().order_by('created_at')  
    return render(request, 'post_details.html', {'post': post, 'comments': comments})

@csrf_exempt
def vote_post(request, post_id, vote_type):
    post = get_object_or_404(Post, id=post_id)
    if vote_type == 'upvote':
        post.upvotes = post.upvotes + 1 if post.upvotes is not None else 1
    elif vote_type == 'downvote':
        post.downvotes = post.downvotes + 1 if post.downvotes is not None else 1
    post.save()
    return JsonResponse({'upvotes': post.upvotes, 'downvotes': post.downvotes})

@csrf_exempt
def vote_comment(request, comment_id, vote_type):
    comment = get_object_or_404(Comment, id=comment_id)
    if vote_type == 'upvote':
        comment.upvotes = comment.upvotes + 1 if comment.upvotes is not None else 1
    elif vote_type == 'downvote':
        comment.downvotes = comment.downvotes + 1 if comment.downvotes is not None else 1
    comment.save()
    return JsonResponse({'upvotes': comment.upvotes, 'downvotes': comment.downvotes})

def vote(request, type, id, vote_type):
    if request.method == 'POST':
        if type == 'post':
            post = Post.objects.get(id=id)
            if vote_type == 'up':
                post.upvotes += 1
            elif vote_type == 'down':
                post.downvotes += 1
            post.save()
            return JsonResponse({'upvotes': post.upvotes, 'downvotes': post.downvotes})

        elif type == 'comment':
            comment = Comment.objects.get(id=id)
            if vote_type == 'up':
                comment.upvotes += 1
            elif vote_type == 'down':
                comment.downvotes += 1
            comment.save()
            return JsonResponse({'upvotes': comment.upvotes, 'downvotes': comment.downvotes})

    return JsonResponse({'error': 'Invalid request'}, status=400)