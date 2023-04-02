from django.contrib import admin
from .models import Profile
from .models import Tag
from .models import Location
from .models import Story
from .models import Like 
from .models import Comment
from .models import Follower

# Register your models here.
admin.site.register(Profile)
admin.site.register(Tag)
admin.site.register(Location)
admin.site.register(Story)
admin.site.register(Like)
admin.site.register(Comment)
admin.site.register(Follower)