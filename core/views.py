from django.shortcuts import render, redirect
from django.contrib.auth.models import User, auth
from django.contrib import messages

from .models import Profile

# Create your views here.


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

                # TODO log user in and redirect to settings page

                # create a profile object for the new user
                user_model = User.objects.get(username=username)
                new_profile = Profile.objects.create(user=user_model, id_user=user_model.id, first_name=user_model.first_name,
                                                     last_name=user_model.last_name, username=user_model.username, email=user_model.email, password=user_model.password)
                new_profile.save()
                # TODO redirect sign in later
                return redirect('signup')
        else:
            messages.info(request, 'Passwords do not match')
            return redirect('signup')

    else:
        return render(request, 'signup.html')

def signin(request):
    if request.method =="POST":
        username= request.POST['username']
        password= request.POST['password']

        user= auth.authenticate(username=username, password=password)
        if user is not None:
            auth.login(request, user)
            return redirect('/')
        else:
            messages.info(request,'Credentials Invalid')
            return redirect('signin')
    else:
        return render(request, 'signin.html')

def logout(request):
    auth.logout(request)
    # TODO redirect to non auth index
    return redirect('signin')