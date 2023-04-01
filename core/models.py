from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

# Create your models here.


class Profile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    id_user = models.IntegerField()
    first_name = models.CharField(max_length=100, default="")
    last_name = models.CharField(max_length=100,  default="")
    username = models.CharField(max_length=50, unique=True, default="")
    email = models.EmailField(unique=True, default="")
    password = models.CharField(max_length=128, default="")
    profile_image = models.ImageField(
        upload_to='profile_images', default='blank-profile-picture.png')
    bio = models.TextField(blank=True)

    def __str__(self):
        return self.user.username
