import json
from django.db import IntegrityError
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.models import User, auth
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import File, Profile, Story, Tag
from django.contrib.gis.geos import Point, Polygon, LineString
from .models import Location

# Create your views here.


@login_required(login_url='signin')
def index(request):
    return render(request, 'index.html')


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
                new_profile = Profile.objects.create(user=user_model, id_user=user_model.id, first_name=user_model.first_name,
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
    DATE_FORMAT_MAPPING = {
        'exact_date': 1,
        'date_range': 2,
        'decade': 3
    }

    if request.method == 'POST':
        user = request.user
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

        print(feature_data)
        locations = []
        for feature in feature_data:
            if feature.get('geometry'):
                location_type = feature['geometry']['type']
                coordinates = feature['geometry']['coordinates']

                if location_type == 'Point':
                    point = Point(coordinates)
                    name = f'Point ({coordinates[0]}, {coordinates[1]})'
                    location = Location(name="test", point=point)

                elif location_type == 'Polygon':
                    polygon = Polygon(coordinates[0])
                    name = f'Polygon ({len(coordinates[0])} points)'
                    location = Location(name="test", area=polygon)

                elif location_type == 'LineString':
                    linestring = LineString(coordinates)
                    name = f'LineString ({len(coordinates)} points)'
                    location = Location(name="test", lines=linestring)

                if location:
                    radius = feature.get('properties', {}).get('radius')
                    if radius:
                        location.radius = float(radius)

                    locations.append(location)
        print(locations)

        # date
        date_format = DATE_FORMAT_MAPPING[date_option]
        if date_format == 1:
            date_exact = request.POST.get('exact_date', None)
            date_range_start = None
            date_range_end = None
            decade = None
        elif date_format == 2:
            date_exact = None
            date_range_start = request.POST.get('start_date', None)
            date_range_end = request.POST.get('end_date', None)
            decade = None
        elif date_format == 3:
            date_exact = None
            date_range_start = None
            date_range_end = None
            decade = request.POST.get('decade', None)

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
            file_obj= File(file=file)
            file_objs.append(file_obj)
                

        print(file_objs)
        print(tag_objs)

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
            decade=decade
        )

        print(story)
        # Save the story object to the database
        story.save()
        story.locations.set(locations)
        story.tags.set(tag_objs)
        story.files.set(file_objs)
        print(story)

    return render(request, 'newpost.html')
