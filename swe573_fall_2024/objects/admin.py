from django.contrib import admin
from .models import Badge, Comment, Post, Tag

admin.site.register(Badge)
admin.site.register(Comment)
# admin.site.register(Post)

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at')
    search_fields = ('title', 'content', 'tags__name')
    filter_horizontal = ('tags',)

admin.site.register(Tag)