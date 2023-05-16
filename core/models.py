from django.contrib.auth import get_user_model
import uuid
from datetime import datetime
from django.contrib.gis.db import models
from ckeditor.fields import RichTextField

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


class Tag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Location(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=255)
    point = models.PointField(blank=True, null=True)
    area = models.PolygonField(null=True, geography=True, blank=True)
    lines = models.LineStringField(blank=True, null=True)
    radius = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.name


class File(models.Model):
    file = models.FileField(upload_to='files')

    def __str__(self):
        return self.file.name


class Story(models.Model):

    DATE_FORMAT_CHOICES = (
        (1, 'Exact Date'),
        (2, 'Range of Dates'),
        (3, 'Decade'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    content = RichTextField(blank=True, null= True)
    created_at = models.DateTimeField(auto_now_add=True)
    date_format = models.IntegerField(choices=DATE_FORMAT_CHOICES, default=1)
    date_exact = models.DateField(null=True, blank=True)
    date_range_start = models.DateField(null=True, blank=True)
    date_range_end = models.DateField(null=True, blank=True)
    decade = models.CharField(max_length=100, null=True, blank=True)
    tags = models.ManyToManyField(Tag, blank=True)
    locations = models.ManyToManyField(Location)
    files = models.ManyToManyField(File, blank=True)
    no_of_likes = models.IntegerField(default=0)
    is_liked_by_current_user = models.BooleanField(default=False)
    no_of_comments = models.IntegerField(default=0)


    def __str__(self):
        return self.title

    def get_comments(self):
        return self.comment_set.all()

    def get_likes(self):
        return self.like_set.all()

    def get_tags(self):
        return self.tags.all()

    def get_locations(self):
        return self.locations.all()

    def get_files(self):
        return self.files.all()


class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    story = models.ForeignKey(Story, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    story = models.ForeignKey(Story, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username


class Follower(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="following")
    follower = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="followers")

    def __str__(self):
        return f"{self.follower.username} follows {self.user.username}"
