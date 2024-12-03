import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from .models import Post, Comment, Object
from .forms import PostForm, CommentForm,  RegistrationForm, RegisterForm
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from PIL import Image
import logging
import spacy
from SPARQLWrapper import SPARQLWrapper, JSON
# from .utils import build_query_from_post, rank_wikidata_results
# from .wikidata_utils import search_wikidata_nlp, build_attributes_for_sparql


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
def create_post(request):
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            # Post oluşturulduktan sonra detay sayfasına yönlendirme
            return redirect('post_details', post_id=post.id)
    else:
        form = PostForm()
    return render(request, 'post_form.html', {'form': form})

# def create_post_ajax(request):
#     if request.method == 'POST':
#         form = PostForm(request.POST, request.FILES)  # Form verilerini ve dosyaları alın
#         if form.is_valid():
#             post = form.save(commit=False)
#             post.author = request.user  # Mevcut kullanıcıyı yazara bağla
#             post.save()

#             # JSON yanıtında image_url bilgisi gönderin
#             return JsonResponse({
#                 'success': True,
#                 'post': {
#                     'id': post.id,
#                     'title': post.title,
#                     'content': post.content,
#                     'author': post.author.username,
#                     'image_url': post.image.url if post.image else None,  # Resim URL'si
#                 }
#             })
#         return JsonResponse({'success': False, 'errors': form.errors}, status=400)

def post_list_ajax(request):
    posts = Post.objects.all()
    return render(request, 'post_list.html', {'posts': posts})


def post_details(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.order_by('created_at')
    results = find_object_from_post(post_id)

    # Mantığı burada belirleyin
    can_mark_as_solved = (
        request.user.is_authenticated and
        (post.author == request.user or request.user.is_superuser) and
        not post.solved
    )

    return render(request, 'post_details.html', {
        'post': post,
        'comments': comments,
        'keywords': results['keywords'],  
        'can_mark_as_solved': can_mark_as_solved,
        'is_homepage': False  # For standalone page
    })

def post_details_partial(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.order_by('created_at')
    results = find_object_from_post(post_id)

    # Mantığı burada belirleyin
    can_mark_as_solved = (
        request.user.is_authenticated and
        (post.author == request.user or request.user.is_superuser) and
        not post.solved
    )

    context = {
        'post': post,
        'comments': comments,
        'keywords': results['keywords'],  
        'can_mark_as_solved': can_mark_as_solved,
        'is_solved': post.solved,
        'is_homepage': True  # For standalone page
    }
    
    # Use the existing post_details.html template
    return render(request, 'post_details.html', context)

def add_comment(request, post_id):
    if request.method == "POST":
        post = get_object_or_404(Post, id=post_id)
        content = request.POST.get("content")
        if content:
            Comment.objects.create(post=post, content=content, user=request.user)
        # Yorum eklendikten sonra detay sayfasına yönlendir
        return redirect('post_detail', post_id=post.id)
    
# def add_comment(request, post_id):
#     if request.method == "POST":
#         post = get_object_or_404(Post, id=post_id)
#         content = request.POST.get("content")
#         if content:
#             # Yeni yorum oluştur
#             comment = Comment.objects.create(post=post, content=content, user=request.user)
#             # Yeni yorumları render et
#             comments_html = render(request, 'partials/comments.html', {'comments': post.comments.all()}).content.decode('utf-8')
#             return JsonResponse({"success": True, "html": comments_html})
#         return JsonResponse({"success": False, "message": "Comment content cannot be empty."})
#     return JsonResponse({"success": False, "message": "Invalid request."})




def vote_comment(request, comment_id, vote_type):
    try:
        comment = Comment.objects.get(id=comment_id)
        
        if comment.post.solved:
            return JsonResponse({
                'success': False,
                'message': 'Cannot vote on comments in solved posts'
            }, status=400)

        if vote_type == 'upvote':
            # Increment upvotes
            if not hasattr(comment, 'upvotes') or comment.upvotes is None:
                comment.upvotes = 0
            comment.upvotes += 1
        elif vote_type == 'downvote':
            # Increment downvotes
            if not hasattr(comment, 'downvotes') or comment.downvotes is None:
                comment.downvotes = 0
            comment.downvotes += 1
        else:
            return JsonResponse({
                'success': False,
                'message': 'Invalid vote type'
            }, status=400)
        
        comment.save()
        
        return JsonResponse({
            'success': True,
            'upvotes': comment.upvotes,
            'downvotes': comment.downvotes
        })
        
    except Comment.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Comment not found'
        }, status=404)
    except Exception as e:
        print(f"Error in vote_comment: {str(e)}")  # For debugging
        return JsonResponse({
            'success': False,
            'message': 'Error processing vote'
        }, status=500)



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


######################### AI Agent ####################


nlp = spacy.load("en_core_web_sm")

def extract_keywords(text):
    """Verilen metinden anahtar kelimeleri çıkarır."""
    if not text:
        print("No text provided to extract_keywords.")
        return []
    
    doc = nlp(text)
    keywords = [token.text.lower() for token in doc if token.is_alpha and not token.is_stop]
    return keywords


# def search_wikidata(keywords):
#     """Wikidata üzerinde anahtar kelimelerle arama yapar ve Post-like sonuçlar döner."""
#     if not keywords:
#         print("No keywords provided for Wikidata search.")
#         return []

#     sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
#     query_keywords = ' '.join(keywords)
#     query = f"""
#     SELECT ?item ?itemLabel ?description
#     WHERE {{
#         ?item ?label "{query_keywords}"@en.
#         OPTIONAL {{ ?item schema:description ?description. FILTER (lang(?description) = "en") }}
#         SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }}
#     }}
#     LIMIT 10
#     """
#     sparql.setQuery(query)
#     sparql.setReturnFormat(JSON)

#     try:
#         results = sparql.query().convert()
#         objects = []
#         for result in results["results"]["bindings"]:
#             objects.append({
#                 "title": result["itemLabel"]["value"],
#                 "content": result.get("description", {}).get("value", "No description available"),
#                 "url": result["item"]["value"]
#             })
#         print("Wikidata search results:", objects)
#         return objects
#     except Exception as e:
#         print(f"Error querying Wikidata: {e}")
#         return []
    


def find_object_from_post(post_id):
    print("find_object_from_post function is called with post_id:", post_id)
    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.all()

    # Post ve yorum içeriklerinden anahtar kelimeleri çıkar
    # print("Post content:", post.content)
    post_keywords = extract_keywords(post.content)
    
    comment_keywords = []
    for comment in comments:
        # print("Comment content:", comment.content)
        comment_keywords.extend(extract_keywords(comment.content))

    all_keywords = list(set(post_keywords + comment_keywords))
    # print("All keywords extracted:", all_keywords)

    # Etiketlerden anahtar kelimeleri ekle
    tag_keywords = [tag.name.lower() for tag in post.tags.all()]
    all_keywords.extend(tag_keywords)

    # Wikidata'da arama yap
    wikidata_results = "No results"    #search_wikidata(all_keywords)
    # print("Wikidata results:", wikidata_results)

    return {
        'keywords': all_keywords,
        'wikidata_results': wikidata_results
    }


# def search_wikidata(keywords):
#     """Wikidata üzerinde anahtar kelimelerle arama yapar."""
#     sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
#     query = f"""
#     SELECT ?item ?itemLabel
#     WHERE {{
#         ?item ?label "{' '.join(keywords)}"@en.
#         SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }}
#     }}
#     LIMIT 10
#     """
#     sparql.setQuery(query)
#     sparql.setReturnFormat(JSON)
#     results = sparql.query().convert()

#     objects = []
#     for result in results["results"]["bindings"]:
#         objects.append({
#             "id": result["item"]["value"],
#             "label": result["itemLabel"]["value"]
#         })
#     return objects

# Wiki Old version

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


# def analyze_post(request, post_id):
#     """
#     Post içeriğini analiz eden ana görünüm.
#     """
#     post = get_object_or_404(Post, id=post_id)

#     # Post özelliklerinden SPARQL sorgusu oluştur
#     attributes = build_attributes_for_sparql(post)

#     # SPARQL sorgusunu çalıştır
#     wikidata_results = search_wikidata_nlp(
#         material=attributes.get("material"),
#         size=attributes.get("size"),
#         color=attributes.get("color"),
#         shape=attributes.get("shape"),
#         weight=attributes.get("weight"),
#         limit=10
#     )
#     print("logg nlp:",search_wikidata_nlp(material="Q11426", size=7, color="Q372669", shape="Q815741", weight=0))
#     return render(request, 'post_analysis.html', {
#         'post': post,
#         'wikidata_results': wikidata_results,
#     })