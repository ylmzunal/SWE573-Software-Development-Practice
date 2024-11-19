from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.conf import settings

class Object(models.Model):
    material = models.CharField(max_length=100)
    # Define other fields here
    # e.g., size, color, etc.

########### 

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class Post(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='posts', null=True, blank=True)
    solved = models.BooleanField(default=False)
    image = models.ImageField(upload_to='post_images/', null=True, blank=True)
    upvotes = models.IntegerField(default=0)  # Add upvotes field
    downvotes = models.IntegerField(default=0)  # Add downvotes field
    tags = models.ManyToManyField(Tag, blank=True) 
    
    material = models.CharField(              # Materyal özelliği
        max_length=100, blank=True, null=True,
        help_text="Cismin materyali (örn: ahşap, plastik, metal)"
    )
    size = models.FloatField(                 # Boyut özelliği
        blank=True, null=True,
        help_text="Cismin boyutu (örneğin: uzunluk, çap)"
    )
    color = models.CharField(                 # Renk özelliği
        max_length=50, blank=True, null=True,
        help_text="Cismin rengi (örn: kırmızı, mavi)"
    )
    shape = models.CharField(                 # Şekil özelliği
        max_length=50, blank=True, null=True,
        help_text="Cismin şekli (örn: küresel, silindirik)"
    )
    weight = models.FloatField(               # Ağırlık özelliği
        blank=True, null=True,
        help_text="Cismin ağırlığı (kg cinsinden)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    
    def __str__(self):
        return self.title

class Comment(models.Model):
    post = models.ForeignKey(Post, related_name='comments', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    upvotes = models.IntegerField(default=0)  # Add upvotes field
    downvotes = models.IntegerField(default=0)  # Add downvotes field

###############
    
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile_data')
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    # Additional fields for badges, ranks, achievements
    badges = models.ManyToManyField('Badge', blank=True)
    rank = models.CharField(max_length=50, blank=True)
    achievements = models.TextField(blank=True)

    def __str__(self):
        return self.user.username
    
class Badge(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='badges/')

    def __str__(self):
        return self.name

class Achievement(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    date_awarded = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} - {self.badge.name}'
    
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True, null=True)
    badges = models.JSONField(default=list, blank=True)  # Örnek bir badges alanı
    achievements = models.JSONField(default=list, blank=True)  # Örnek bir achievements alanı

    def __str__(self):
        return f"{self.user.username}'s Profile"