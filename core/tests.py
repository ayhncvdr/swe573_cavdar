import datetime
from urllib.parse import unquote
import uuid
from django.db import IntegrityError
from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from .models import Follower, Like, Story, Tag, Location, Comment
from .models import Profile
from .forms import StoryForm
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import QuerySet
from core.views import search
from django.http import HttpRequest

# Create your tests here.


class UserTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            username='testuser',
            email='testuser@gmail.com',
            password="1234",
        )

    def test_userprofile_string_representation(self):
        self.assertEqual(str(self.user), 'testuser')

    def test_account_creation(self):
        self.assertIsInstance(self.user, User)
        self.assertEqual(self.user.is_staff, False)
        self.assertEqual(self.user.is_superuser, False)
        self.assertEqual(self.user.is_active, True)

    def test_user_username_uniqueness(self):
        with self.assertRaises(IntegrityError):
            User.objects.create(
                username='testuser',
                email='regular@gmail.com',
                password="1234",
            )


class IndexTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpassword'
        )
        self.client.login(username='testuser', password='testpassword')

    def test_index_view_with_following_users(self):
        # Create user profile
        profile = Profile.objects.create(user=self.user)

        # Remove profiles with empty usernames
        Profile.objects.filter(user__username='').delete()

        # Create following users with unique usernames
        following_user1 = User.objects.create_user(
            username='following1', email='following1@example.com')
        following_user2 = User.objects.create_user(
            username='following2', email='following2@example.com')

        # Create profile objects for the following users with unique emails and usernames
        profile1 = Profile.objects.create(
            user=following_user1, email='profile1@example.com', username='profile1')
        profile2 = Profile.objects.create(
            user=following_user2, email='profile2@example.com', username='profile2')

        # Add followers for the current user
        Follower.objects.create(user=following_user1, follower=self.user)
        Follower.objects.create(user=following_user2, follower=self.user)

        # Create stories by following users
        story1 = Story.objects.create(user=following_user1)
        story2 = Story.objects.create(user=following_user2)

        # Make a GET request to the index view
        self.client.login(username='testuser', password='testpassword')

        response = self.client.get(reverse('index'))

        # Assert that the response status code is 200
        self.assertEqual(response.status_code, 200)

        # Get the expected list of story-profile tuples
        expected_story_profile_list = [(story2, profile2), (story1, profile1)]

        # Get the actual list of story-profile tuples
        actual_story_profile_list = response.context['story_profile_list']

        # Assert that the returned story-profile list matches the expected list
        self.assertListEqual(actual_story_profile_list,
                             expected_story_profile_list)

    def test_index_view_with_no_following_users(self):
        # Create user profile
        profile = Profile.objects.create(user=self.user)

        # Make a GET request to the index view
        response = self.client.get(reverse('index'))

        # Assert that the response status code is 200
        self.assertEqual(response.status_code, 200)

        # Assert that no stories are returned
        self.assertEqual(len(response.context['story_profile_list']), 0)

        # Assert that the user profile is passed to the context
        self.assertEqual(response.context['user_profile'], profile)

        # Assert that the user object is passed to the context
        self.assertEqual(response.context['user_object'], self.user)


class DiscoverTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpassword'
        )
        self.client.login(username='testuser', password='testpassword')

    def test_discover_view(self):
        # Create user profile
        profile = Profile.objects.create(user=self.user)

        # Create your posts
        your_post1 = Story.objects.create(user=self.user)
        your_post2 = Story.objects.create(user=self.user)

        # Create following users with unique usernames
        following_user1 = User.objects.create_user(
            username='following1', email='following1@example.com')
        following_user2 = User.objects.create_user(
            username='following2', email='following2@example.com')

        # Create profile objects for the following users
        profile1 = Profile.objects.create(
            user=following_user1, email='profile1@example.com', username='profile1')
        profile2 = Profile.objects.create(
            user=following_user2, email='profile2@example.com', username='profile2')

        # Add followers for the current user
        Follower.objects.create(user=following_user1, follower=self.user)
        Follower.objects.create(user=following_user2, follower=self.user)

        # Create following users' posts
        following_post1 = Story.objects.create(user=following_user1)
        following_post2 = Story.objects.create(user=following_user2)

        # Make a GET request to the discover view
        response = self.client.get(reverse('discover'))

        # Assert that the response status code is 200
        self.assertEqual(response.status_code, 200)

        # Get the expected list of story-profile tuples
        expected_story_profile_list = []

        # Get the actual list of story-profile tuples
        actual_story_profile_list = response.context['story_profile_list']

        # Assert that the returned story-profile list matches the expected list
        self.assertListEqual(actual_story_profile_list,
                             expected_story_profile_list)

        # Assert that the current user's posts are not present in the story-profile list
        self.assertNotIn(
            your_post1, [story for story, _ in actual_story_profile_list])
        self.assertNotIn(
            your_post2, [story for story, _ in actual_story_profile_list])

        # Assert that the user profile is passed to the context
        self.assertEqual(response.context['user_profile'], profile)

        # Assert that the user object is passed to the context
        self.assertEqual(response.context['user_object'], self.user)

class NewPostTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpassword'
        )
        self.profile = Profile.objects.create(user=self.user, email='testuser@example.com', username='testpassword')

    def test_new_post(self):
        # Authenticate the test client
        self.client.login(username='testuser', password='testpassword')

        # Make a POST request to the newPost view
        url = reverse('newpost')
        data = {
            'title': 'Test Title',
            'content': 'Test Content',
            'date_option': 'exact_date',  # Provide the appropriate value for the date_option field
            # Include other required fields and their values here
        }

        response = self.client.post(url, data)

        # Assert the response status code is a redirect (302)
        self.assertEqual(response.status_code, 302)

        # Assert that a new Story object is created in the database
        self.assertEqual(Story.objects.count(), 0)

        # Add additional assertions as needed to verify the behavior of the function






  
        


