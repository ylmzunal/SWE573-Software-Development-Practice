from django.db import models

class Object(models.Model):
    material = models.CharField(max_length=100)
    # Define other fields here
    # e.g., size, color, etc.