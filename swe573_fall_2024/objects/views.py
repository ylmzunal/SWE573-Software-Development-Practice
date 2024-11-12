import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.http import HttpResponse
from .models import Post, Comment
from .forms import PostForm, CommentForm
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
from .forms import RegistrationForm
from django.contrib.auth.decorators import login_required
from django.db.models import Q

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
    posts = Post.objects.all().order_by('-created_at')
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


def add_comment(request, post_id):
    post = Post.objects.get(id=post_id)
    if request.method == 'POST':
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.post = post
            comment.save()
            return redirect('homepage')
    else:
        comment_form = CommentForm()
    context = {'comment_form': comment_form, 'post': post}
    return render(request, 'add_comment.html', context)

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

def profile_view(request, username):
    user = get_object_or_404(User, username=username)
    profile = user.profile
    context = {
        'user': user,
        'profile': profile,
        # Include other context data as needed
    }
    return render(request, 'profile.html', context)


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Log the user in after registration
            return redirect('home')  # Redirect to 'home' after successful registration
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

# Profile view
def profile(request, user_id):
    user = get_object_or_404(User, id=user_id)
    return render(request, 'profile.html', {'profile_user': user})

@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user  # Assign the logged-in user to the post
            post.save()
            return redirect('home')
    else:
        form = PostForm()
    return render(request, 'create_post.html', {'form': form})