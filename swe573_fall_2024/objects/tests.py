from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Post, Comment

class SearchViewTests(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(username='testuser', password='12345')
        
        # Create a test post
        self.post = Post.objects.create(
            title='Test Post',
            content='Test content',
            author=self.user,
            material='metal',
            color='blue',
            shape='round'
        )
        
        # Create a test comment
        self.comment = Comment.objects.create(
            post=self.post,
            user=self.user,
            content='Test comment with specific keyword'
        )
        
        self.client = Client()

    def test_search_in_comments(self):
        # Test searching within comments
        response = self.client.get(reverse('search_view'), {'q': 'specific keyword'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Post')  # Should find the post via comment

    def test_search_in_posts(self):
        # Test searching within post content
        response = self.client.get(reverse('search_view'), {'q': 'Test content'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Post')

    def test_wikidata_search(self):
        # Test wikidata search with comments
        response = self.client.get(reverse('wikidata_search'), {
            'q': 'specific keyword',
            'post_id': self.post.id
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Post')

    def test_empty_search(self):
        # Test empty search
        response = self.client.get(reverse('search_view'), {'q': ''})
        self.assertEqual(response.status_code, 200)

    def test_combined_search(self):
        # Test searching in both posts and comments
        response = self.client.get(reverse('search_view'), {'q': 'Test'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Post')
