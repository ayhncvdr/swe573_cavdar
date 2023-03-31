from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

# Create your models here.


class Profile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    id_user = models.IntegerField()
    # INFO: these will be from django auth
    # first_name = models.CharField(max_length=100)
    # last_name = models.CharField(max_length=100)
    # username = models.CharField(max_length=50, unique=True)
    # email = models.EmailField(unique=True)
    # password = models.CharField(max_length=128)
    profile_image = models.ImageField(
        upload_to='profile_images', default='blank-profile-picture.png')
    bio = models.TextField(blank=True)

    def __str__(self):
        return self.user.username
