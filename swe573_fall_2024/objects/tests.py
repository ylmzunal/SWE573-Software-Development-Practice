from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Post, Comment, Profile
from django.core.files.uploadedfile import SimpleUploadedFile

class ObjectFinderTests(TestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create profile for test user
        self.profile = Profile.objects.create(
            user=self.user,
            bio='Test bio'
        )
        
        # Create a test post
        self.post = Post.objects.create(
            title='Test Post',
            content='Test content',
            author=self.user,
            material='Metal',
            size='10',
            color='Red',
            shape='Round',
            weight='100'
        )
        
        # Create test comment
        self.comment = Comment.objects.create(
            post=self.post,
            user=self.user,
            content='Test comment'
        )
        
        # Set up test client
        self.client = Client()

    def test_homepage_view(self):
        response = self.client.get(reverse('homepage'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'homepage.html')
        self.assertContains(response, 'Object Finder')

    def test_post_creation(self):
        self.client.login(username='testuser', password='testpass123')
        
        post_data = {
            'title': 'New Test Post',
            'content': 'New test content',
            'material': 'Wood',
            'size': '20',
            'color': 'Blue',
            'shape': 'Square',
            'weight': '200'
        }
        
        response = self.client.post(reverse('create_post'), post_data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful creation
        self.assertTrue(Post.objects.filter(title='New Test Post').exists())

    def test_post_detail_view(self):
        response = self.client.get(reverse('post_details', args=[self.post.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'post_details.html')
        self.assertContains(response, 'Test Post')

    def test_comment_creation(self):
        self.client.login(username='testuser', password='testpass123')
        
        comment_data = {
            'content': 'New test comment'
        }
        
        response = self.client.post(
            reverse('add_comment', args=[self.post.id]),
            comment_data
        )
        self.assertEqual(response.status_code, 302)  # Redirect after successful creation
        self.assertTrue(Comment.objects.filter(content='New test comment').exists())

    def test_profile_view(self):
        response = self.client.get(reverse('profile', args=[self.user.username]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profile.html')
        self.assertContains(response, 'testuser')

    def test_bio_update(self):
        self.client.login(username='testuser', password='testpass123')
        
        new_bio = 'Updated bio text'
        response = self.client.post(reverse('update_bio'), {'bio': new_bio})
        
        # Check if the request was successful
        self.assertEqual(response.status_code, 200)
        
        # Refresh profile from database
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.bio, new_bio)

    def test_post_solved_status(self):
        self.client.login(username='testuser', password='testpass123')
        
        # Test marking post as solved
        response = self.client.post(reverse('mark_as_solved', args=[self.post.id]))
        self.assertEqual(response.status_code, 200)
        
        # Refresh post from database
        self.post.refresh_from_db()
        self.assertTrue(self.post.solved)

    def test_comment_voting(self):
        self.client.login(username='testuser', password='testpass123')
        
        # Test upvote
        response = self.client.post(
            reverse('vote_comment', args=[self.comment.id, 'upvote'])
        )
        self.assertEqual(response.status_code, 200)
        
        # Refresh comment from database
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.upvotes, 1)

    def test_unauthorized_access(self):
        # Test accessing create post without login
        response = self.client.get(reverse('create_post'))
        self.assertEqual(response.status_code, 302)  # Should redirect to login

    def test_search_functionality(self):
        response = self.client.get(reverse('search_view'), {'q': 'Test'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Post')

    def test_post_validation(self):
        self.client.login(username='testuser', password='testpass123')
        
        # Test creating post without required fields
        post_data = {'title': ''}  # Missing required fields
        response = self.client.post(reverse('create_post'), post_data)
        self.assertEqual(response.status_code, 200)  # Should stay on same page
        self.assertFalse(Post.objects.filter(title='').exists())

    def test_profile_creation(self):
        new_user = User.objects.create_user(
            username='newuser',
            password='newpass123'
        )
        # Profile should be created automatically
        self.assertTrue(Profile.objects.filter(user=new_user).exists())