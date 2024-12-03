from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.conf import settings


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class Object(models.Model):
    name = models.CharField(max_length=255, default="Unnamed Object")
    description = models.TextField(blank=True, null=True)  # Obje açıklaması
    tags = models.ManyToManyField(Tag, blank=True)  # Etiketlerle ilişki

    # Dinamik özellikler
    material = models.CharField(max_length=100, blank=True, null=True)
    size = models.FloatField(blank=True, null=True)
    color = models.CharField(max_length=50, blank=True, null=True)
    shape = models.CharField(max_length=50, blank=True, null=True)
    weight = models.FloatField(blank=True, null=True)

    # created_at = models.DateTimeField(auto_now_add=True, default=timezone.now)  # Varsayılan olarak mevcut zaman
    # updated_at = models.DateTimeField(auto_now=True)
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # Object nesnesini önce kaydet
        self.add_tags()

    def add_tags(self):
        """
        `material`, `color`, vb. alanlardan otomatik olarak tag oluşturur ve ilişkilendirir.
        """
        tag_fields = [self.material, self.color, self.shape]
        for field in tag_fields:
            if field:
                tag, created = Tag.objects.get_or_create(name=field)
                self.tags.add(tag)

        # Boyut ve ağırlık için özel formatlı etiketler oluştur
        if self.size:
            tag, created = Tag.objects.get_or_create(name=f"Size: {self.size}cm")
            self.tags.add(tag)
        if self.weight:
            tag, created = Tag.objects.get_or_create(name=f"Weight: {self.weight}kg")
            self.tags.add(tag)

    def __str__(self):
       return self.name

########### 

class Post(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='posts', null=True, blank=True)
    image = models.ImageField(upload_to='post_images/', null=True, blank=True)
    upvotes = models.IntegerField(default=0)  # Add upvotes field
    downvotes = models.IntegerField(default=0)  # Add downvotes field
    tags = models.ManyToManyField(Tag, blank=True) 
    matched_object = models.TextField(blank=True, null=True)  # Sonuç: Tavsiye edilen nesne
    solved = models.BooleanField(default=False)
    solved_at = models.DateTimeField(null=True, blank=True)

    def mark_as_solved(self):
        self.solved = True
        self.solved_at = timezone.now()
        self.save()
    
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

    
    def save(self, *args, **kwargs):
        # Post nesnesini önce kaydet
        super().save(*args, **kwargs)
        self.add_tags()  # Otomatik etiketleme

    def add_tags(self):
        """
        Post'un özelliklerinden otomatik olarak etiket oluştur ve ekle.
        """
        tag_fields = [self.material, self.color, self.shape]
        for field in tag_fields:
            if field:  # Eğer alan boş değilse
                tag, created = Tag.objects.get_or_create(name=field)
                self.tags.add(tag)

        # Boyut ve ağırlık gibi özellikleri özel formatta ekle
        if self.size:
            tag, created = Tag.objects.get_or_create(name=f"Size: {self.size}cm")
            self.tags.add(tag)
        if self.weight:
            tag, created = Tag.objects.get_or_create(name=f"Weight: {self.weight}kg")
            self.tags.add(tag)

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
    bio = models.TextField(max_length=500, blank=True, default='')
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