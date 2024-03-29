import json
import os
import geojson
from django.db import IntegrityError
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.contrib.auth.models import User, auth
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import File, Profile, Story, Tag, Like, Comment, Follower
from django.contrib.gis.geos import Point, Polygon, LineString
from .models import Location
from .forms import StoryForm
from datetime import datetime
from django.test import TestCase, Client
from dotenv import load_dotenv
from geopy.geocoders import Nominatim

load_dotenv()

# Create your views here.

def reverse_geocode_nominatim(lat, lon):
    geolocator = Nominatim(user_agent="my_app")
    location = geolocator.reverse(f"{lat}, {lon}")
    print(location)
    return location


@login_required(login_url='signin')
def index(request):
    user_object = User.objects.get(username=request.user.username)
    user_profile = Profile.objects.get(user=user_object)

    # Get the users you are following
    following_users = Follower.objects.filter(
        follower=user_object).values_list('user', flat=True)

    # Get the stories of the following users
    stories = Story.objects.filter(
        user__in=following_users).order_by('-created_at')

    # Create a list to store tuples of story and profile
    story_profile_list = []

    # Iterate over each story and fetch the profile object
    for story in stories:
        user_story_object = User.objects.get(username=story.user.username)
        likes = Like.objects.filter(story=story)
        comments = Comment.objects.filter(story=story)
        try:
            user_story_profile = Profile.objects.get(user=user_story_object)
        except Profile.DoesNotExist:
            user_story_profile = None

        story_profile_list.append((story, user_story_profile))

    context = {
        'story_profile_list': story_profile_list,
        'user_profile': user_profile,
        'user_object': user_object
    }
    return render(request, 'index.html', context)


@login_required(login_url='signin')
def discover(request):
    user_object = User.objects.get(username=request.user.username)
    user_profile = Profile.objects.get(user=user_object)

    # Get your posts
    your_posts = Story.objects.filter(user=user_object)

    # Get the users you are following
    following_users = Follower.objects.filter(
        follower=user_object).values_list('user', flat=True)

    # Get the stories of the users you are following
    following_posts = Story.objects.filter(user__in=following_users)

    # Get all other stories except your posts and the following posts
    stories = Story.objects.exclude(user=user_object).exclude(
        user__in=following_users).order_by('-created_at')

    # Create a list to store tuples of story and profile
    story_profile_list = []

    # Iterate over each story and fetch the profile object
    for story in stories:
        user_story_object = User.objects.get(username=story.user.username)
        likes = Like.objects.filter(story=story)
        comments = Comment.objects.filter(story=story)
        try:
            user_story_profile = Profile.objects.get(user=user_story_object)
        except Profile.DoesNotExist:
            user_story_profile = None

        story_profile_list.append((story, user_story_profile))

    context = {
        'story_profile_list': story_profile_list,
        'user_profile': user_profile,
        'user_object': user_object
    }
    return render(request, 'discover.html', context)


@login_required(login_url='signin')
def search(request):
    user_object = User.objects.get(username=request.user.username)
    user_profile = Profile.objects.get(user=user_object)
    query = request.GET.get('query')

    # Check if query parameter is provided
    if query:
        # Search profiles
        profile_query = Q(
            Q(user__username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(bio__icontains=query)
        )
        profiles = Profile.objects.filter(profile_query).distinct()

        # Search stories
        story_query = Q(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(tags__name__icontains=query) |
            Q(locations__name__icontains=query) |
            Q(date_exact__icontains=query) |
            Q(date_range_start__icontains=query) |
            Q(date_range_end__icontains=query) |
            Q(decade__icontains=query) |
            Q(exact_date_and_time__icontains=query)
        )

        # Search for stories matching the decade
        if query.endswith('s') and len(query) == 5 and query[:-1].isdigit():
            decade = query[:-1]
            decade_start = datetime.strptime(decade, '%Y')
            decade_end = datetime.strptime(str(int(decade) + 9), '%Y')
            story_query |= Q(decade__icontains=decade) | (
                Q(date_exact__gte=decade_start, date_exact__lt=decade_end) |
                Q(date_range_start__gte=decade_start, date_range_start__lt=decade_end) |
                Q(date_range_end__gte=decade_start, date_range_end__lt=decade_end) |
                Q(exact_date_and_time__gte=decade_start,
                  exact_date_and_time__lt=decade_end)
            )

        stories = Story.objects.filter(story_query).distinct()
        story_profile_list = []
        for story in stories:
            user_story_object = User.objects.get(username=story.user.username)
            try:
                user_story_profile = Profile.objects.get(
                    user=user_story_object)
            except Profile.DoesNotExist:
                user_story_profile = None

            story_profile_list.append((story, user_story_profile))

        context = {
            'query': query,
            'profiles': profiles,
            'stories': stories,
            'user_profile': user_profile,
            'user_object': user_object,
            'story_profile_list': story_profile_list
        }
    else:
        # Handle case when query parameter is not provided
        context = {
            'query': '',
            'profiles': [],
            'stories': [],
            'user_profile': user_profile,
            'user_object': user_object,
            'story_profile_list': []
        }

    return render(request, 'search.html', context)


@login_required(login_url='signin')
def postDetailed(request):
    story_id = request.GET.get('story_id')
    profile_id = request.GET.get('profile_id')
    user_object = User.objects.get(username=request.user.username)
    user_profile = Profile.objects.get(user=user_object)

    try:
        story = Story.objects.get(id=story_id)
        likes = Like.objects.filter(story=story)
        comments = Comment.objects.filter(story=story)
        profile = Profile.objects.get(id=profile_id) if profile_id else None
        return render(request, 'postdetailed.html', {'story': story, 'profile': profile, 'user_profile': user_profile, 'likes': likes, 'comments': comments})
    except Story.DoesNotExist:
        return HttpResponse(story_id)
    except Profile.DoesNotExist:
        return HttpResponse("Profile not found")
    except User.DoesNotExist:
        return HttpResponse("User not found")


@login_required(login_url='signin')
def profile(request, pk):
    current_user = User.objects.get(username=request.user.username)
    current_profile = Profile.objects.get(user=current_user)
    user_object = User.objects.get(username=pk)
    try:
        user_profile = Profile.objects.get(user=user_object)
    except Profile.DoesNotExist:
        user_profile = None
        # Handle the profile not found case, e.g., display an error message or redirect to a different page

    user_posts = Story.objects.filter(user=user_object).order_by('-created_at')
    user_posts_length = len(user_posts)

    follower = current_user
    user = user_object

    if Follower.objects.filter(follower=follower, user=user).first():
        button_text = 'Unfollow'
    else:
        button_text = 'Follow'

    user_followers = Follower.objects.filter(user=user_object)
    user_followers_count = len(user_followers)
    user_following = Follower.objects.filter(follower=user_object)
    user_following_count = len(user_following)

    context = {
        'current_user': current_user,
        'current_profile': current_profile,
        'user_object': user_object,
        'user_profile': user_profile,
        'user_posts': user_posts,
        'user_posts_length': user_posts_length,
        'button_text': button_text,
        'user_followers': user_followers,
        'user_followers_count': user_followers_count,
        'user_following': user_following,
        'user_following_count': user_following_count,
    }
    return render(request, 'profile.html', context)


@login_required(login_url='signin')
def usersFollowers(request):
    user_name = request.GET.get('user_name')
    user_object = User.objects.get(username=user_name)
    current_user = User.objects.get(username=request.user.username)
    current_profile = Profile.objects.get(user=current_user)
    followers = Follower.objects.filter(user=user_object)
    context = {
        'followers': followers,
        'current_user': current_user,
        'current_profile': current_profile
    }
    return render(request, 'followers.html', context)


@login_required(login_url='signin')
def usersFollowing(request):
    user_name = request.GET.get('user_name')
    user_object = User.objects.get(username=user_name)
    current_user = User.objects.get(username=request.user.username)
    current_profile = Profile.objects.get(user=current_user)
    followers = Follower.objects.filter(follower=user_object)
    context = {
        'followers': followers,
        'current_user': current_user,
        'current_profile': current_profile
    }
    return render(request, 'following.html', context)


@login_required(login_url='signin')
def usersLiked(request):
    story_id = request.GET.get('story_id')
    profile_id = request.GET.get('profile_id')
    user_object = User.objects.get(username=request.user.username)
    user_profile = Profile.objects.get(user=user_object)
    try:
        story = Story.objects.get(id=story_id)
        likes = Like.objects.filter(story=story)
        profile = Profile.objects.get(id=profile_id) if profile_id else None
        return render(request, 'usersliked.html', {'story': story, 'profile': profile, 'user_profile': user_profile, 'likes': likes})
    except Story.DoesNotExist:
        return HttpResponse(story_id)
    except Profile.DoesNotExist:
        return HttpResponse("Profile not found")
    except User.DoesNotExist:
        return HttpResponse("User not found")


@login_required(login_url='signin')
def usersCommented(request):
    story_id = request.GET.get('story_id')
    profile_id = request.GET.get('profile_id')
    user_object = User.objects.get(username=request.user.username)
    user_profile = Profile.objects.get(user=user_object)
    try:
        story = Story.objects.get(id=story_id)
        comments = Comment.objects.filter(story=story)
        profile = Profile.objects.get(id=profile_id) if profile_id else None
        return render(request, 'userscommented.html', {'story': story, 'profile': profile, 'user_profile': user_profile, 'comments': comments})
    except Story.DoesNotExist:
        return HttpResponse(story_id)
    except Profile.DoesNotExist:
        return HttpResponse("Profile not found")
    except User.DoesNotExist:
        return HttpResponse("User not found")


@login_required(login_url='signin')
def like_post(request):
    story_id = request.GET.get('story_id')
    user_object = User.objects.get(username=request.user.username)

    if story_id:
        story = Story.objects.get(id=story_id)
        like_filter = Like.objects.filter(
            story=story, user=user_object).first()
        if like_filter is None:
            new_like = Like.objects.create(story=story, user=user_object)
            new_like.save()
            story.no_of_likes += 1
            story.is_liked_by_current_user = True
            story.save()
        else:
            like_filter.delete()
            story.no_of_likes -= 1
            story.is_liked_by_current_user = False
            story.save()

    # Get the URL of the current page
    current_page = request.META.get('HTTP_REFERER')
    if current_page:
        return HttpResponseRedirect(current_page)
    else:
        return redirect('/')


@login_required(login_url='signin')
def comment_post(request):
    if request.method == 'POST':
        content = request.POST.get('comment')
        story_id = request.POST.get('story_id')
        user_object = User.objects.get(username=request.user.username)
        if content and story_id:
            story = Story.objects.get(id=story_id)
            comment = Comment.objects.create(
                user=user_object, content=content, story=story)
            comment.save()
            story.no_of_comments += 1
            story.save()

    # Get the URL of the current page
    current_page = request.META.get('HTTP_REFERER')
    if current_page:
        return HttpResponseRedirect(current_page)
    else:
        return redirect('/')


@login_required(login_url='signin')
def delete_story(request):
    story_id = request.GET.get('story_id')
    story = Story.objects.get(id=story_id)
    if story.user == request.user:
        story.delete()

    current_page = request.META.get('HTTP_REFERER')
    if current_page:
        return HttpResponseRedirect(current_page)
    else:
        return redirect('/')


@login_required(login_url='signin')
def follow(request):
    if request.method == 'POST':
        follower_username = request.POST['follower']
        user_username = request.POST['user']

        follower = User.objects.get(username=follower_username)
        user = User.objects.get(username=user_username)

        if Follower.objects.filter(follower=follower, user=user).exists():
            delete_follower = Follower.objects.get(
                follower=follower, user=user)
            delete_follower.delete()
            return redirect('/profile/' + user.username)
        else:
            new_follower = Follower.objects.create(
                follower=follower, user=user)
            return redirect('/profile/' + user.username)

    else:
        return redirect('/')


def signup(request):
    if request.method == 'POST':
        firstname = request.POST['First Name']
        lastname = request.POST['Last Name']
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        password2 = request.POST['password2']

        if password == password2:
            if User.objects.filter(email=email).exists():
                messages.info(request, 'Email already exists')
                return redirect('signup')
            elif User.objects.filter(username=username).exists():
                messages.info(request, 'Username already exists')
                return redirect('signup')
            else:
                user = User.objects.create_user(
                    username=username, email=email, password=password, first_name=firstname, last_name=lastname)
                user.save()

                # log user in and redirect to settings page
                user_login = auth.authenticate(
                    username=username, password=password)
                auth.login(request, user_login)

                # create a profile object for the new user
                user_model = User.objects.get(username=username)
                new_profile = Profile.objects.create(user=user_model, first_name=user_model.first_name,
                                                     last_name=user_model.last_name, username=user_model.username, email=user_model.email, password=user_model.password)
                new_profile.save()
                # TODO redirect setting page later
                return redirect('settings')
        else:
            messages.info(request, 'Passwords do not match')
            return redirect('signup')

    else:
        return render(request, 'signup.html')


def signin(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']

        user = auth.authenticate(username=username, password=password)
        if user is not None:
            auth.login(request, user)
            return redirect('/')
        else:
            messages.info(request, 'Credentials Invalid')
            return redirect('signin')
    else:
        return render(request, 'signin.html')


@login_required(login_url='signin')
def logout(request):
    auth.logout(request)
    # TODO design sign in as non auth user page + login
    return redirect('signin')


@login_required(login_url='signin')
def settings(request):
    user_profile = Profile.objects.get(user=request.user)
    if request.method == 'POST':
        if request.FILES.get('image') == None:
            image = user_profile.profile_image
            bio = request.POST['bio']
            first_name = request.POST['first_name']
            last_name = request.POST['last_name']

            user_profile.profile_image = image
            user_profile.bio = bio
            user_profile.first_name = first_name
            user_profile.last_name = last_name
            user_profile.save()
        else:
            image = request.FILES.get('image')
            bio = request.POST['bio']
            first_name = request.POST['first_name']
            last_name = request.POST['last_name']

            user_profile.profile_image = image
            user_profile.bio = bio
            user_profile.first_name = first_name
            user_profile.last_name = last_name
            user_profile.save()

        return redirect('index')

    return render(request, 'settings.html', {'user_profile': user_profile})


@login_required(login_url='signin')
def newPost(request):
    form = StoryForm()
    user_object = User.objects.get(username=request.user.username)
    user_profile = Profile.objects.get(user=user_object)
    DATE_FORMAT_MAPPING = {
        'exact_date': 1,
        'date_range': 2,
        'decade': 3,
        'exact_date_and_time': 4
    }

    if request.method == 'POST':
        user = request.user
        form = StoryForm(request.POST)
        title = request.POST['title']
        content = request.POST['content']
        date_option = request.POST['date_option']
        tags_str = request.POST.get('tags', '[]')
        if tags_str:
            tags_list = json.loads(tags_str)
        else:
            tags_list = []
        files = request.FILES.getlist('files', None)
        feature_data_str = request.POST.get('features', '[]')
        if feature_data_str:
            feature_data = json.loads(feature_data_str)
        else:
            feature_data = []

        locations = []
        for feature in feature_data:
            if feature.get('geometry'):
                location_type = feature['geometry']['type']
                coordinates = feature['geometry']['coordinates']

                if location_type == 'Point':
                    point = Point(coordinates)
                    results = reverse_geocode_nominatim(point.y, point.x)
                    location_name = results
                    
                    radius = feature.get('properties', {}).get('radius')
                    if radius:
                        location = Location(
                            name="Circle Area in " + str(location_name), point=point)
                        location.radius = float(radius)
                    else:
                        location = Location(name=str(location_name), point=point)

                elif location_type == 'Polygon':
                    polygon = Polygon(coordinates[0])
                    centroid = polygon.centroid
                    results =  reverse_geocode_nominatim(centroid.y, centroid.x)
                    location_name = results
                    
                    location = Location(
                        name="Area Around "+str(location_name), area=polygon)

                elif location_type == 'LineString':
                    linestring = LineString(coordinates)
                    midpoint = linestring.interpolate(linestring.length/2)
                    results = reverse_geocode_nominatim(midpoint.y, midpoint.x)
                    location_name = results
                    location = Location(
                        name="Lines Around "+str(location_name), lines=linestring)

                if location:
                    locations.append(location)

        # date
        date_format = DATE_FORMAT_MAPPING[date_option]
        if date_format == 1:
            date_exact = request.POST.get('exact_date', None)
            date_range_start = None
            date_range_end = None
            decade = None
            exact_date_and_time = None
        elif date_format == 2:
            date_exact = None
            date_range_start = request.POST.get('start_date', None)
            date_range_end = request.POST.get('end_date', None)
            decade = None
            exact_date_and_time = None

        elif date_format == 3:
            date_exact = None
            date_range_start = None
            date_range_end = None
            decade = request.POST.get('decade', None)
            exact_date_and_time = None
        elif date_format == 4:
            date_exact = None
            date_range_start = None
            date_range_end = None
            decade = None
            exact_date_and_time = request.POST.get('exact_date_and_time', None)

        # Validation checks
        if not content:
            messages.error(request, 'Content is required.')
            return redirect('newpost')

        if not title:
            messages.error(request, 'Title is required.')
            return redirect('newpost')

        if not locations:
            messages.error(request, 'At least one location is required.')
            return redirect('newpost')

        if date_format == 1:
            if not date_exact:
                messages.error(request, 'Exact date is required.')
                return redirect('newpost')

        elif date_format == 2:
            if not date_range_start or not date_range_end:
                messages.error(
                    request, 'Start date and end date are required.')
                return redirect('newpost')

        elif date_format == 3:
            if not decade:
                messages.error(request, 'Decade is required.')
                return redirect('newpost')
        elif date_format == 4:
            if not exact_date_and_time:
                messages.error(request, 'Exact date and time is required.')
                return redirect('newpost')
        else:
            messages.error(request, 'Invalid date option.')
            return redirect('newpost')

        # tags
        tag_objs = []
        for tag in tags_list:
            tag_name = tag.get('value', None)
            if tag_name:
                tag_obj = Tag(name=tag_name)
                tag_objs.append(tag_obj)

        # file_objs
        file_objs = []
        for file in files:
            file_obj = File(file=file)
            file_objs.append(file_obj)



        # Save all the Location objects to the database
        for location in locations:
            location.save()

        # Save all the Tag objects to the database
        for tag in tag_objs:
            tag.save()

        # Save all the File objects to the database
        for file in file_objs:
            file.save()

        story = Story(
            user=user,
            title=title,
            content=content,
            date_format=date_format,
            date_exact=date_exact,
            date_range_start=date_range_start,
            date_range_end=date_range_end,
            decade=decade,
            exact_date_and_time=exact_date_and_time
        )

        # Save the story object to the database
        story.save()
        story.locations.set(locations)
        story.tags.set(tag_objs)
        story.files.set(file_objs)
        return redirect('index')

    context = {
        'form': form,
        'user_profile': user_profile
    }

    return render(request, 'newpost.html', context=context)
