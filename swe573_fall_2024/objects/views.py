import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from .models import Post, Comment, Object, Profile, PostFeature, Vote
from .forms import PostForm, CommentForm, RegistrationForm, RegisterForm, MATERIAL_CHOICES, COLOR_CHOICES, SHAPE_CHOICES
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from django.urls import reverse
from django.views.decorators.http import require_POST
from PIL import Image
import logging
from SPARQLWrapper import SPARQLWrapper, JSON
# from .utils import build_query_from_post, rank_wikidata_results
# from .wikidata_utils import search_wikidata_nlp, build_attributes_for_sparql
import json
from django.contrib import messages
import os
from django.conf import settings


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

    # Get all posts with comment count
    posts = Post.objects.annotate(comment_count=Count('comments')).all().order_by('-created_at')
    
    # For each post, get its comments and their vote counts
    for post in posts:
        comments = Comment.objects.filter(post=post).select_related('user').order_by('-created_at')
        
        for comment in comments:
            # Get vote counts
            upvotes = Vote.objects.filter(comment=comment, vote_type='up').count()
            downvotes = Vote.objects.filter(comment=comment, vote_type='down').count()
            
            # Get user's vote if logged in
            user_vote = None
            if request.user.is_authenticated:
                user_vote = Vote.objects.filter(
                    user=request.user, 
                    comment=comment
                ).values_list('vote_type', flat=True).first()
            
            comment.upvotes = upvotes
            comment.downvotes = downvotes
            comment.user_vote = user_vote
        
        post.comments_list = comments

    context = {
        'post_form': post_form,
        'posts': posts,
        'is_homepage': True
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
        badges.append("Active Poster ������������")
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
        post_data = request.POST.copy()
        
        # Convert comma-separated strings to lists for multiple choice fields
        for field in ['material', 'color', 'shape']:
            if post_data.get(field):
                values = post_data.get(field).split(',')
                post_data.setlist(field, values)
        
        form = PostForm(post_data, request.FILES)
        print("Files in request:", request.FILES)  # Debug print
        
        if form.is_valid():
            try:
                post = form.save(commit=False)
                post.author = request.user
                
                # Handle image upload
                if 'image' in request.FILES:
                    print("Processing image upload...")
                    image_file = request.FILES['image']
                    print(f"Received image: {image_file.name}, size: {image_file.size}")
                    
                    # Generate a unique filename
                    import uuid
                    file_extension = os.path.splitext(image_file.name)[1]
                    unique_filename = f"{uuid.uuid4()}{file_extension}"
                    
                    # Create the post_images directory if it doesn't exist
                    upload_path = os.path.join('post_images', unique_filename)
                    full_path = os.path.join(settings.MEDIA_ROOT, 'post_images')
                    os.makedirs(full_path, exist_ok=True)
                    
                    # Save the file locally
                    with open(os.path.join(settings.MEDIA_ROOT, upload_path), 'wb+') as destination:
                        for chunk in image_file.chunks():
                            destination.write(chunk)
                    
                    # Update post
                    post.image = upload_path
                    print("Updated post image path:", post.image)
                
                # Store the selections as comma-separated strings
                post.material = ','.join(post_data.getlist('material'))
                post.color = ','.join(post_data.getlist('color'))
                post.shape = ','.join(post_data.getlist('shape'))
                
                post.save()
                print("Post saved successfully")
                messages.success(request, 'Post created successfully!')
                return redirect('homepage')
                
            except Exception as e:
                print(f"Error occurred: {type(e).__name__}")
                print(f"Error details: {str(e)}")
                import traceback
                print(f"Traceback:\n{traceback.format_exc()}")
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


def post_list_ajax(request):
    posts = Post.objects.all()
    return render(request, 'post_list.html', {'posts': posts})


def post_details(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = Comment.objects.filter(post=post).select_related('user').order_by('-created_at')
    
    # Get vote counts and user votes for each comment
    for comment in comments:
        # Get vote counts
        upvotes = Vote.objects.filter(comment=comment, vote_type='up').count()
        downvotes = Vote.objects.filter(comment=comment, vote_type='down').count()
        
        # Get user's vote if logged in
        user_vote = None
        if request.user.is_authenticated:
            user_vote = Vote.objects.filter(
                user=request.user, 
                comment=comment
            ).values_list('vote_type', flat=True).first()
        
        comment.upvotes = upvotes
        comment.downvotes = downvotes
        comment.user_vote = user_vote
    
    context = {
        'post': post,
        'comments': comments,
        'comment_count': comments.count(),
        'is_homepage': False,
        'can_edit': request.user.is_authenticated and request.user == post.author,  # Only post author can edit
        'can_mark_solved': request.user.is_authenticated and request.user == post.author and not post.solved  # Only post author can mark as solved
    }
    
    return render(request, 'post_details.html', context)

def post_details_partial(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = Comment.objects.filter(post=post).select_related('user').order_by('-created_at')
    results = find_object_from_post(post_id)

    # Get vote counts and user votes for each comment
    for comment in comments:
        # Get vote counts
        upvotes = Vote.objects.filter(comment=comment, vote_type='up').count()
        downvotes = Vote.objects.filter(comment=comment, vote_type='down').count()
        
        # Get user's vote if logged in
        user_vote = None
        if request.user.is_authenticated:
            user_vote = Vote.objects.filter(
                user=request.user, 
                comment=comment
            ).values_list('vote_type', flat=True).first()
        
        comment.upvotes = upvotes
        comment.downvotes = downvotes
        comment.user_vote = user_vote

    context = {
        'post': post,
        'comments': comments,
        'keywords': results['keywords'],
        'can_edit': request.user.is_authenticated and request.user == post.author,  # Only post author can edit
        'can_mark_solved': request.user.is_authenticated and request.user == post.author and not post.solved,  # Only post author can mark as solved
        'is_solved': post.solved,
        'is_homepage': True
    }
    
    return render(request, 'post_details.html', context)

@login_required
def add_comment(request, post_id):
    if request.method == 'POST':
        post = get_object_or_404(Post, id=post_id)
        content = request.POST.get('content')
        
        if content:
            try:
                comment = Comment.objects.create(
                    post=post,
                    user=request.user,
                    content=content
                )
                print(f"Comment created successfully: {comment.id}")
                messages.success(request, 'Comment added successfully!')
            except Exception as e:
                print(f"Error creating comment: {str(e)}")
                messages.error(request, 'Error adding comment. Please try again.')
        else:
            messages.error(request, 'Comment content cannot be empty.')
            
    return redirect('post_details', post_id=post_id)

@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    
    if request.method == 'POST':
        try:
            # Handle image upload first
            if 'image' in request.FILES:
                image = request.FILES['image']
                # Generate a unique filename
                import uuid
                file_extension = os.path.splitext(image.name)[1]
                unique_filename = f"{uuid.uuid4()}{file_extension}"
                
                # Create the post_images directory if it doesn't exist
                upload_path = os.path.join('post_images', unique_filename)
                full_path = os.path.join(settings.MEDIA_ROOT, 'post_images')
                os.makedirs(full_path, exist_ok=True)
                
                # Save the file locally
                with open(os.path.join(settings.MEDIA_ROOT, upload_path), 'wb+') as destination:
                    for chunk in image.chunks():
                        destination.write(chunk)
                
                # Update post
                post.image = upload_path
                post.save()
            
            # Update other fields
            post.title = request.POST.get('title', post.title)
            post.content = request.POST.get('content', post.content)
            post.material = ','.join(request.POST.getlist('material'))
            post.color = ','.join(request.POST.getlist('color'))
            post.shape = ','.join(request.POST.getlist('shape'))
            post.size = request.POST.get('size', post.size)
            post.weight = request.POST.get('weight', post.weight)
            
            post.save()
            
            messages.success(request, 'Post updated successfully!')
            return redirect('post_details', post_id=post.id)
            
        except Exception as e:
            print(f"Error occurred: {type(e).__name__}")
            print(f"Error details: {str(e)}")
            import traceback
            print(f"Traceback:\n{traceback.format_exc()}")
            messages.error(request, f'Error updating post: {str(e)}')
    
    form = PostForm(instance=post)
    context = {
        'form': form,
        'post': post,
        'material_choices': MATERIAL_CHOICES,
        'color_choices': COLOR_CHOICES,
        'shape_choices': SHAPE_CHOICES,
    }
    return render(request, 'objects/edit_post.html', context)

@login_required
def edit_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    
    # Check if user is the comment author
    if request.user != comment.user:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    if request.method == 'POST':
        new_content = request.POST.get('content')
        if new_content:
            comment.content = new_content
            comment.last_edited_by = request.user
            comment.save()
            return JsonResponse({
                'success': True,
                'content': comment.content,
                'edited_at': comment.updated_at.strftime('%B %d, %Y, %I:%M %p')
            })
        return JsonResponse({'error': 'Content cannot be empty'}, status=400)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)



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


@login_required
def vote_comment(request, comment_id, vote_type):
    if request.method == 'POST':
        try:
            comment = get_object_or_404(Comment, id=comment_id)
            
            # Debug print
            print(f"Processing vote: Comment {comment_id}, Type {vote_type}, User {request.user}")
            
            # Check for existing vote
            existing_vote = Vote.objects.filter(user=request.user, comment=comment).first()
            
            if existing_vote:
                if existing_vote.vote_type == vote_type:
                    # If voting the same way, remove the vote
                    existing_vote.delete()
                    print(f"Removed existing {vote_type} vote")
                else:
                    # If voting differently, update the vote
                    existing_vote.vote_type = vote_type
                    existing_vote.save()
                    print(f"Changed vote to {vote_type}")
            else:
                # Create new vote
                Vote.objects.create(
                    user=request.user,
                    comment=comment,
                    vote_type=vote_type
                )
                print(f"Created new {vote_type} vote")
            
            # Get updated counts
            upvotes = Vote.objects.filter(comment=comment, vote_type='up').count()
            downvotes = Vote.objects.filter(comment=comment, vote_type='down').count()
            
            # Get user's current vote
            current_vote = Vote.objects.filter(
                user=request.user, 
                comment=comment
            ).values_list('vote_type', flat=True).first()
            
            print(f"Updated counts - Upvotes: {upvotes}, Downvotes: {downvotes}")
            print(f"User's current vote: {current_vote}")
            
            return JsonResponse({
                'success': True,
                'upvotes': upvotes,
                'downvotes': downvotes,
                'user_vote': current_vote
            })
            
        except Exception as e:
            print(f"Error processing vote: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)
            
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
    
    
def extract_keywords(content):
    # Örnek: Basit anahtar kelime çıkarımı
    if not content:
        return []
    words = content.split()
    keywords = [word for word in words if len(word) > 3]  # Uzunluğu 3'ten fazla olan kelimeleri al
    return keywords

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
    query = request.GET.get('q', '').strip()
    local_results = Post.objects.none()
    tag_results = Post.objects.none()
    wikidata_results = []

    if query:
        # First, find all comments that match the search term
        matching_comments = Comment.objects.filter(content__icontains=query)
        
        # Get the posts that have matching comments
        posts_with_matching_comments = Post.objects.filter(comments__in=matching_comments)
        
        # Get posts that match the search term directly
        matching_posts = Post.objects.filter(
            Q(title__icontains=query) | 
            Q(content__icontains=query)
        )
        
        # Combine the results
        local_results = (matching_posts | posts_with_matching_comments).distinct()
        
        # Search in tags
        tag_results = Post.objects.filter(tags__name__icontains=query).distinct()
        
        # Debug prints
        print(f"Query: {query}")
        print(f"Matching comments found: {matching_comments.count()}")
        for comment in matching_comments:
            print(f"Comment match: '{comment.content[:50]}...' in post {comment.post.id}")
        print(f"Posts with matching comments: {posts_with_matching_comments.count()}")
        print(f"Direct post matches: {matching_posts.count()}")
        print(f"Total unique results: {local_results.count()}")

        # Get Wikidata results
        wikidata_results = search_wikidata(query)

    context = {
        'query': query,
        'local_results': local_results,
        'tag_results': tag_results,
        'wikidata_results': wikidata_results,
    }
    return render(request, 'search_results.html', context)



def edit_comment_view(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    post = comment.post  # Get the post from the comment
    
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            comment.content = content
            comment.save()
            return redirect('post_details', post_id=post.id)
    
    return render(request, 'objects/edit_comment.html', {
        'comment': comment,
        'post': post
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
        # First, find all comments that match the search term
        matching_comments = Comment.objects.filter(content__icontains=query)
        
        # Get posts with matching comments
        posts_with_matching_comments = Post.objects.filter(comments__in=matching_comments)
        
        # Get posts that match directly
        matching_posts = Post.objects.filter(
            Q(title__icontains=query) | 
            Q(content__icontains=query)
        )
        
        # Combine results
        local_results = (matching_posts | posts_with_matching_comments).distinct()

        # Get tag results
        tag_results = Post.objects.filter(tags__name__icontains=query).distinct()

        # Add filter properties to search if post_id exists
        if post_id:
            try:
                post = Post.objects.get(id=post_id)
                print("Post found:", post)
                
                # Helper function to clean string list values
                def clean_list_string(value):
                    if value:
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
        'local_results': local_results,
        'tag_results': tag_results,
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

