from django.urls import path
from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('signup', views.signup, name='signup'),
    path('signin', views.signin, name='signin'),
    path('logout', views.logout, name='logout'),
    path('settings', views.settings, name='settings'),
    path('newpost', views.newPost, name='newpost'),
    path('postdetailed', views.postDetailed, name='postdetailed'),
    path('like-post', views.like_post, name="like-post"),
    path('usersliked', views.usersLiked, name ='usersliked'),
    path('comment-post', views.comment_post, name="comment-post")
]
