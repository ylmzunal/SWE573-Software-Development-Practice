from django import forms
from .models import Post, Comment
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        exclude = ['author']
        fields = ['title', 'content', 'material', 'size', 'color', 'shape', 'weight', 'image']  # Formda kullanılacak alanlar
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Post Başlığı'}),
            'content': forms.Textarea(attrs={'placeholder': 'Post İçeriği'}),
            'material': forms.TextInput(attrs={'placeholder': 'Materyal'}),
            'size': forms.NumberInput(attrs={'placeholder': 'Boyut (cm)'}),
            'color': forms.TextInput(attrs={'placeholder': 'Renk'}),
            'shape': forms.TextInput(attrs={'placeholder': 'Şekil'}),
            'weight': forms.NumberInput(attrs={'placeholder': 'Ağırlık (kg)'}),
        }



    # def __init__(self, *args, **kwargs):
    #     self.user = kwargs.pop('user', None)  # Kullanıcıyı formdan al
    #     super(PostForm, self).__init__(*args, **kwargs)

    # def clean(self):
    #     cleaned_data = super().clean()
    #     if not self.user or not self.user.is_authenticated:
    #         raise forms.ValidationError("Giriş yapmış olmanız gerekiyor.")
    #     return cleaned_data

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']

# forms.py

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class RegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    password_confirm = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")
        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', "Passwords do not match")
        return cleaned_data