import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from .models import Post, Comment
from .forms import PostForm, CommentForm,  RegistrationForm, RegisterForm
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from PIL import Image
import logging


logger = logging.getLogger(__name__)

def homepage(request):
    if request.method == 'POST':
        post_form = PostForm(request.POST, request.FILES)
        if post_form.is_valid():
            post = post_form.save(commit=False)
            post.author = request.user
            post.save()
            return JsonResponse({
                'success': True,
                'post': {
                    'id': post.id,
                    'title': post.title,
                    'content': post.content,
                }
            })
        return JsonResponse({'success': False, 'error': 'Invalid form submission'})
    else:
        post_form = PostForm()

    posts = Post.objects.annotate(comment_count=Count('comments')).all().order_by('-created_at')
    context = {
        'post_form': post_form,
        'posts': posts
    }
    return render(request, 'homepage.html', context)


@login_required
def profile_view(request, username):
    user = get_object_or_404(User, username=username)

    # Fetch user-related data
    posts = Post.objects.filter(author=user)
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

def create_post_form(request):
    form = PostForm()
    return render(request, 'post_form.html', {'form': form})

@login_required
def create_post_ajax(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)  # Form verilerini ve dosyaları alın
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user  # Mevcut kullanıcıyı yazara bağla
            post.save()

            # JSON yanıtında image_url bilgisi gönderin
            return JsonResponse({
                'success': True,
                'post': {
                    'id': post.id,
                    'title': post.title,
                    'content': post.content,
                    'author': post.author.username,
                    'image_url': post.image.url if post.image else None,  # Resim URL'si
                }
            })
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)

def post_list_ajax(request):
    posts = Post.objects.all()
    return render(request, 'post_list.html', {'posts': posts})


def post_details(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.order_by('created_at')

    # Mantığı burada belirleyin
    can_mark_as_solved = (
        request.user.is_authenticated and
        (post.author == request.user or request.user.is_superuser) and
        not post.solved
    )

    return render(request, 'post_details.html', {
        'post': post,
        'comments': comments,
        'can_mark_as_solved': can_mark_as_solved,
    })


def add_comment(request, post_id):
    if request.method == 'POST':
        post = get_object_or_404(Post, id=post_id)

        if post.solved:
            return JsonResponse({'success': False, 'message': 'Comments are disabled for this post as it is marked as solved.'}, status=403)

        content = request.POST.get('content', '').strip()
        if content:
            comment = Comment.objects.create(
                post=post,
                user=request.user if request.user.is_authenticated else None,
                content=content
            )
            return JsonResponse({
                'success': True,
                'comment': {
                    'content': comment.content,
                    'author': comment.user.username if comment.user else 'Anonymous',
                    'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                }
            })
        return JsonResponse({'success': False, 'message': 'Comment content cannot be empty.'}, status=400)
    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=400)



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



def search_wikidata(query):
    """
    Query the Wikidata API for multiple words and combine results.
    :param query: The search term (can include multiple words)
    :return: A list of dictionaries with 'label', 'description', and 'url' from Wikidata
    """
    query_terms = query.replace(",", " ").split()  # Virgülleri ve fazla boşlukları temizle
    all_results = []  # Tüm sonuçları biriktirmek için liste

    url = "https://www.wikidata.org/w/api.php"

    for term in query_terms:  # Her kelime için ayrı sorgu gönder
        params = {
            'action': 'wbsearchentities',
            'format': 'json',
            'language': 'en',
            'search': term
        }
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                for item in data.get('search', []):
                    result = {
                        'label': item.get('label'),
                        'description': item.get('description'),
                        'url': f"https://www.wikidata.org/wiki/{item.get('id')}"
                    }
                    if result not in all_results:  # Sonuçları tekrar eklemeden biriktir
                        all_results.append(result)
        except requests.exceptions.RequestException as e:
            print(f"Wikidata API error: {e}")

    return all_results




def search_view(request):
    """
    Search functionality for both local Post model and Wikidata API.
    """
    query = request.GET.get('q', '').strip()  # Kullanıcıdan gelen sorgu
    local_results = Post.objects.none()  # Varsayılan olarak boş queryset
    tag_results = Post.objects.none()  # Varsayılan olarak boş queryset
    wikidata_results = []

    if query:
        # Yerel sonuçları getir
        terms = query.replace(",", " ").split()  # Çok kelimeli sorguyu parçalara ayır
        for term in terms:
            local_results = local_results | Post.objects.filter(
                Q(title__icontains=term) | Q(content__icontains=term)
            )

        # Etiket sonuçlarını getir
        for term in terms:
            tag_results = tag_results | Post.objects.filter(
                Q(tags__name__icontains=term)
            )

        # Wikidata sonuçlarını getir
        wikidata_results = search_wikidata(query)

    context = {
        'query': query,
        'local_results': local_results.distinct(),
        'tag_results': tag_results.distinct(),
        'wikidata_results': wikidata_results,
    }
    return render(request, 'search_results.html', context)


@csrf_exempt
def vote_comment(request, comment_id, action):
    if request.method == 'POST' and request.user.is_authenticated:
        comment = get_object_or_404(Comment, id=comment_id)
        if action == 'upvote':
            comment.upvotes += 1
        elif action == 'downvote':
            comment.downvotes += 1
        comment.save()
        return JsonResponse({
            'success': True,
            'upvotes': comment.upvotes,
            'downvotes': comment.downvotes,
        })
    return JsonResponse({'success': False, 'error': 'Invalid request or not authenticated.'})

@login_required
def mark_as_solved(request, post_id):
    if request.method == 'POST':
        post = get_object_or_404(Post, id=post_id)

        # Yalnızca post sahibi veya admin işaretleyebilir
        if post.author == request.user or request.user.is_superuser:
            post.solved = True
            post.save()
            return JsonResponse({'success': True, 'message': 'Post marked as solved.'})
        return JsonResponse({'success': False, 'message': 'You are not authorized to mark this post as solved.'}, status=403)
    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=400)