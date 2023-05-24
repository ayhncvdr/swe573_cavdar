import datetime
from urllib.parse import unquote
import uuid
from django.db import IntegrityError
from django.test import TestCase, Client
from django.urls import reverse
from .models import Follower, Like, Story, Tag, Location, Comment
from .models import Profile
from .forms import StoryForm
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import QuerySet

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
            following_user1 = User.objects.create_user(username='following1', email='following1@example.com')
            following_user2 = User.objects.create_user(username='following2', email='following2@example.com')

            # Create profile objects for the following users with unique emails and usernames
            profile1 = Profile.objects.create(user=following_user1, email='profile1@example.com', username='profile1')
            profile2 = Profile.objects.create(user=following_user2, email='profile2@example.com', username='profile2')

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

            print("Expected List:")
            print(expected_story_profile_list)

            print("Actual List:")
            print(actual_story_profile_list)

            # Assert that the returned story-profile list matches the expected list
            self.assertListEqual(actual_story_profile_list, expected_story_profile_list)

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
