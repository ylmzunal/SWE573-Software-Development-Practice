from django import forms
from .models import Post, Comment, Profile
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

MATERIAL_CHOICES = [
    ('', 'None'),  # Default option
    ('Metal', 'Metal'),
    ('Wood', 'Wood'),
    ('Glass', 'Glass'),
    ('Plastic', 'Plastic'),
    ('Stone', 'Stone'),
    ('Ceramic', 'Ceramic'),
    ('Platinum', 'Platinum'),
    ('Gold', 'Gold'),
    ('Copper', 'Copper'),
    ('Iron', 'Iron'),
    ('Natural material', 'Natural material'),
    ('Synthetic material', 'Synthetic material'),
]

COLOR_CHOICES = [
    ('', 'None'),  # Default option
    ('White', 'White'),
    ('Black', 'Black'),
    ('Red', 'Red'),
    ('Blue', 'Blue'),
    ('Green', 'Green'),
    ('Yellow', 'Yellow'),
    ('Purple', 'Purple'),
    ('Orange', 'Orange'),
    ('Pink', 'Pink'),
    ('Brown', 'Brown'),
    ('Gray', 'Gray'),
]

SHAPE_CHOICES = [
    ('', 'None'),  # Default option
    ('Rectangle', 'Rectangle'),
    ('Square', 'Square'),
    ('Circle', 'Circle'),
    ('Triangle', 'Triangle'),
    ('Oval', 'Oval'),
    ('Sphere', 'Sphere'),
    ('Pyramid', 'Pyramid'),
    ('Cylinder', 'Cylinder'),
    ('Hexagon', 'Hexagon'),
    ('Pentagon', 'Pentagon'),
    ('Octagon', 'Octagon'),
    ('Cube', 'Cube'),
]

class PostForm(forms.ModelForm):
    material = forms.ChoiceField(
        choices=MATERIAL_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    color = forms.ChoiceField(
        choices=COLOR_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    shape = forms.ChoiceField(
        choices=SHAPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    size = forms.FloatField(
        required=False,
        widget=forms.NumberInput(attrs={'placeholder': 'Size (cm)', 'class': 'form-control'})
    )
    weight = forms.FloatField(
        required=False,
        widget=forms.NumberInput(attrs={'placeholder': 'Weight (kg)', 'class': 'form-control'})
    )

    class Meta:
        model = Post
        fields = ['title', 'content', 'material', 'size', 'color', 'shape', 'weight', 'image']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Post Title'}),
            'content': forms.Textarea(attrs={'placeholder': 'Post Content'}),
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']

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

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['profile_picture']