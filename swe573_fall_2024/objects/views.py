import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from .models import Post, Comment, Object, Profile, PostFeature
from .forms import PostForm, CommentForm, RegistrationForm, RegisterForm, MATERIAL_CHOICES, COLOR_CHOICES, SHAPE_CHOICES
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from PIL import Image
import logging
import spacy
from SPARQLWrapper import SPARQLWrapper, JSON
# from .utils import build_query_from_post, rank_wikidata_results
# from .wikidata_utils import search_wikidata_nlp, build_attributes_for_sparql
import json
from django.contrib import messages


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
    user_profile = get_object_or_404(User, username=username)
    posts = Post.objects.filter(author=user_profile).order_by('-created_at')
    comments = Comment.objects.filter(user=user_profile).order_by('-created_at')
    
    # Calculate statistics
    total_posts = posts.count()
    total_comments = comments.count()
    total_upvotes = sum(comment.upvotes or 0 for comment in comments)
    total_downvotes = sum(comment.downvotes or 0 for comment in comments)
    
    # Calculate badges
    badges = []
    if total_posts >= 5:
        badges.append("Active Poster ��������")
    if total_comments >= 10:
        badges.append("Helpful Commenter 💬")
    if total_upvotes >= 10:
        badges.append("Popular Contributor 👍")
    
    # Calculate achievements
    solved_posts = posts.filter(solved=True)
    solved_posts_count = solved_posts.count()
    achievements = [
        {
            'title': 'Problem Solver',
            'description': f'Solved {solved_posts_count} posts',
            'icon': '✓'
        }
    ]

    context = {
        'user_profile': user_profile,
        'posts': posts,
        'total_posts': total_posts,
        'total_comments': total_comments,
        'total_upvotes': total_upvotes,
        'total_downvotes': total_downvotes,
        'bio': user_profile.profile.bio if hasattr(user_profile, 'profile') else None,
        'badges': badges,
        'achievements': achievements,
        'solved_posts_count': solved_posts_count,
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
    if request.method == 'POST':
        post_data = request.POST.copy()  # Make a mutable copy of the POST data
        
        # Convert comma-separated strings to lists for multiple choice fields
        for field in ['material', 'color', 'shape']:
            if post_data.get(field):
                values = post_data.get(field).split(',')
                post_data.setlist(field, values)  # Set as list of individual values
        
        form = PostForm(post_data, request.FILES)
        print("Modified POST data:", post_data)
        
        if form.is_valid():
            try:
                post = form.save(commit=False)
                post.author = request.user
                
                # Store the selections as comma-separated strings in the model
                post.material = ','.join(post_data.getlist('material'))
                post.color = ','.join(post_data.getlist('color'))
                post.shape = ','.join(post_data.getlist('shape'))
                
                post.save()
                messages.success(request, 'Post created successfully!')
                return redirect('homepage')
            except Exception as e:
                print(f"Error saving post: {e}")
                messages.error(request, f'Error creating post: {str(e)}')
        else:
            print("Form errors:", form.errors)
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = PostForm()

    context = {
        'form': form,
        'material_choices': [choice for choice in MATERIAL_CHOICES if choice[0]],
        'color_choices': [choice for choice in COLOR_CHOICES if choice[0]],
        'shape_choices': [choice for choice in SHAPE_CHOICES if choice[0]],
    }
    
    return render(request, 'post_form.html', context)

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
    comments = post.comments.all().order_by('created_at')  # Get all comments for this post
    
    # Convert the string representations to lists if they exist
    materials = post.material.split(',') if post.material else []
    colors = post.color.split(',') if post.color else []
    shapes = post.shape.split(',') if post.shape else []
    
    context = {
        'post': post,
        'comments': comments,  # Add comments to context
        'material': post.material,
        'color': post.color,
        'shape': post.shape,
    }
    return render(request, 'post_details.html', context)

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

@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    
    # Check if user is authorized to edit
    if post.author != request.user and not request.user.is_superuser:
        return redirect('post_details', post_id=post_id)
    
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            edited_post = form.save(commit=False)
            edited_post.last_edited_by = request.user
            edited_post.save()
            form.save_m2m()  # Save many-to-many relationships (for tags)
            return redirect('post_details', post_id=post_id)
    else:
        form = PostForm(instance=post)
    
    context = {
        'form': form,
        'post': post,
        'is_homepage': False
    }
    
    return render(request, 'objects/edit_post.html', context)

@login_required
def edit_comment(request, comment_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'})
    
    comment = get_object_or_404(Comment, id=comment_id)
    
    # Check if user is authorized to edit
    if comment.user != request.user and not request.user.is_superuser:
        return JsonResponse({'success': False, 'message': 'Not authorized to edit this comment'})
    
    try:
        data = json.loads(request.body)
        content = data.get('content', '').strip()
        
        if not content:
            return JsonResponse({'success': False, 'message': 'Comment content cannot be empty'})
        
        comment.content = content
        comment.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Comment updated successfully'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })



def get_wikidata_label(qid):
    if not qid or not qid.startswith('Q'):
        return None
        
    url = f"https://www.wikidata.org/w/api.php"
    params = {
        'action': 'wbgetentities',
        'ids': qid,
        'format': 'json',
        'props': 'labels',
        'languages': 'en'
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        if 'entities' in data and qid in data['entities']:
            entity = data['entities'][qid]
            if 'labels' in entity and 'en' in entity['labels']:
                return entity['labels']['en']['value']
    except:
        return None
    return None


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




@login_required
def vote_comment(request, comment_id, vote_type):
    if request.method == 'POST':
        comment = get_object_or_404(Comment, id=comment_id)
        user = request.user
        
        # Get current vote counts
        upvotes = comment.upvotes or 0
        downvotes = comment.downvotes or 0
        
        # Store previous vote state to determine if we're toggling
        was_upvoted = False
        was_downvoted = False
        
        if vote_type == 'upvote':
            if comment.upvotes and comment.upvotes > 0:
                # If already upvoted, remove the upvote
                comment.upvotes = comment.upvotes - 1
                was_upvoted = True
            else:
                # Add new upvote
                comment.upvotes = (comment.upvotes or 0) + 1
                # Remove downvote if exists
                if comment.downvotes and comment.downvotes > 0:
                    comment.downvotes = comment.downvotes - 1
        else:  # downvote
            if comment.downvotes and comment.downvotes > 0:
                # If already downvoted, remove the downvote
                comment.downvotes = comment.downvotes - 1
                was_downvoted = True
            else:
                # Add new downvote
                comment.downvotes = (comment.downvotes or 0) + 1
                # Remove upvote if exists
                if comment.upvotes and comment.upvotes > 0:
                    comment.upvotes = comment.upvotes - 1
        
        comment.save()
        
        return JsonResponse({
            'success': True,
            'upvotes': comment.upvotes or 0,
            'downvotes': comment.downvotes or 0,
            'userVoteStatus': {
                'hasUpvoted': vote_type == 'upvote' and not was_upvoted,
                'hasDownvoted': vote_type == 'downvote' and not was_downvoted
            }
        })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    }, status=400)



@login_required
def mark_as_solved(request, post_id):
    if request.method == 'POST':
        post = get_object_or_404(Post, id=post_id)
        
        # Only allow the post author to mark as solved/unsolved
        if request.user != post.author:
            return JsonResponse({
                'success': False,
                'message': 'Only the post author can mark this post as solved or unsolved.'
            }, status=403)
        
        # Toggle the solved status
        post.solved = not post.solved
        post.save()
        
        return JsonResponse({
            'success': True,
            'solved': post.solved,
            'message': f'Post has been marked as {"solved" if post.solved else "unsolved"}!'
        })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method.'
    }, status=400)


@login_required
@require_POST
def update_bio(request):
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'message': 'You must be logged in to update your bio'
        }, status=403)
    
    try:
        bio = request.POST.get('bio', '').strip()
        
        # Get or create user profile
        profile, created = Profile.objects.get_or_create(user=request.user)
        profile.bio = bio
        profile.save()
        
        return JsonResponse({
            'success': True,
            'bio': bio or 'No bio available.'
        })
    except Exception as e:
        print(f"Error updating bio: {str(e)}")  # For debugging
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

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
#     })@login_required
def edit_comment_view(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            comment.content = content
            comment.save()
            return redirect('post_details', post_id=post.id)  # Use post.id for redirect
    
    return render(request, 'objects/edit_comment.html', {
        'comment': comment,
        'post': post  # Add post to context
    })

@login_required
def mark_post_status(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    
    # Check if user is the author of the post
    if request.user == post.author:
        post.solved = not post.solved  # Toggle the solved status
        post.save()
    
    return redirect('post_detail', post_id=post_id)

def wikidata_search(request):
    query = request.GET.get('q', '')
    filter_types = request.GET.getlist('filter_type')
    post_id = request.GET.get('post_id')
    
    print("Original query:", query)
    print("Selected filters:", filter_types)
    print("Post ID:", post_id)
    
    search_query = query
    local_results = Post.objects.none()
    tag_results = Post.objects.none()
    wikidata_results = []

    if query:
        # Get local results
        terms = query.replace(",", " ").split()
        for term in terms:
            local_results = local_results | Post.objects.filter(
                Q(title__icontains=term) | Q(content__icontains=term)
            )

        # Get tag results
        for term in terms:
            tag_results = tag_results | Post.objects.filter(
                Q(tags__name__icontains=term)
            )

        # Add filter properties to search if post_id exists
        if post_id:
            try:
                post = Post.objects.get(id=post_id)
                print("Post found:", post)
                
                # Helper function to clean string list values
                def clean_list_string(value):
                    if value:
                        # Remove brackets, quotes, and split by comma
                        cleaned = value.strip('[]').replace("'", "").split(',')
                        return [item.strip() for item in cleaned]
                    return []

                # Process each selected filter
                if 'color' in filter_types and post.color:
                    colors = clean_list_string(post.color)
                    search_query += ' ' + ' '.join(colors)
                    print("Added colors:", colors)
                
                if 'material' in filter_types and post.material:
                    materials = clean_list_string(post.material)
                    search_query += ' ' + ' '.join(materials)
                    print("Added materials:", materials)
                    
                if 'shape' in filter_types and post.shape:
                    shapes = clean_list_string(post.shape)
                    search_query += ' ' + ' '.join(shapes)
                    print("Added shapes:", shapes)
                    
                if 'weight' in filter_types and post.weight:
                    search_query += f' {post.weight}'
                    print("Added weight:", post.weight)
                    
                if 'size' in filter_types and post.size:
                    search_query += f' {post.size}'
                    print("Added size:", post.size)
                    
            except Post.DoesNotExist:
                print("Post not found!")
                pass

        print("Final search query:", search_query)
        # Get Wikidata results
        wikidata_results = search_wikidata(search_query)

    context = {
        'query': query,
        'local_results': local_results.distinct(),
        'tag_results': tag_results.distinct(),
        'wikidata_results': wikidata_results,
    }
    
    return render(request, 'search_results.html', context)

def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    
    # Extract Q-IDs from the URLs
    material_qid = post.material.split('/')[-1] if post.material else None
    color_qid = post.color.split('/')[-1] if post.color else None
    shape_qid = post.shape.split('/')[-1] if post.shape else None
    
    # Get labels for each property
    material = get_wikidata_label(material_qid) or "Not specified"
    color = get_wikidata_label(color_qid) or "Not specified"
    shape = get_wikidata_label(shape_qid) or "Not specified"
    
    context = {
        'post': post,
        'material': material,
        'color': color,
        'shape': shape,
    }
    
    return render(request, 'post_details.html', context)

def post_form_view(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            # Your existing form processing code
            pass
    else:
        form = PostForm()

    context = {
        'form': form,
        'material_choices': MATERIAL_CHOICES[1:],  # Skip the 'None' option
        'color_choices': COLOR_CHOICES[1:],        # Skip the 'None' option
        'shape_choices': SHAPE_CHOICES[1:],        # Skip the 'None' option
    }
    return render(request, 'post_form.html', context)

