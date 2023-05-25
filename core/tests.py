import datetime
from urllib.parse import unquote
import uuid
from django.db import IntegrityError
from django.test import TestCase, Client, RequestFactory
from django.urls import reverse

from memorycloud.settings import AUTH_PASSWORD_VALIDATORS
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
        self.user = User.objects.create_user(
            username='testuser', email='testuser@example.com', password='testpass')
        self.user_profile = Profile.objects.create(user=self.user)
        self.client.login(username='testuser', password='testpass')
        self.story = Story.objects.create(
            title='Test Title', user=self.user, content='Test Content', date_format=1)

    def test_new_post(self):
        url = reverse('newpost')
        data = {
            'title': 'Test Title',
            'content': 'Test Content',
            'date_option': 'exact_date',
            'exact_date': '2022-01-01',
            'tags': '[{"value": "Test Tag"}]',
            'files': '',
            'features': ''
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        story_filter = Story.objects.filter(title='Test Title').first()
        self.assertIsNotNone(story_filter)
        self.assertEqual(story_filter.content, 'Test Content')


class LikePostViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',  email='testuser@example.com', password='testpass')
        self.user_profile = Profile.objects.create(user=self.user)
        self.story = Story.objects.create(
            title='Test Story', user=self.user, content='Test Content', date_format=1)
        self.like = Like.objects.create(
            story=self.story, user=self.user)

    def test_like_post(self):
        self.client.login(username='testuser', password='testpass')
        url = reverse('like-post')
        response = self.client.get(url, {'story_id': self.story.id})
        self.assertEqual(response.status_code, 302)
        like_filter = Like.objects.filter(
            story=self.story, user=self.user).first()
        if like_filter is None:
            new_like = Like.objects.create(story=self.story, user=self.user)
            new_like.save()
            self.story.no_of_likes += 1
            self.story.is_liked_by_current_user = True
            self.story.save()
        else:
            like_filter.delete()
            self.story.no_of_likes -= 1
            self.story.is_liked_by_current_user = False
            self.story.save()
        self.assertRedirects(response, '/')

class CommentPostTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', email='testuser@example.com', password='testpass')
        self.story = Story.objects.create(
            title='Test Story', content='Test Content', user=self.user, date_format=1)
        self.client.login(username='testuser', password='testpass')

    def test_comment_post(self):
        url = reverse('comment-post')
        data = {'comment': 'Test Comment', 'story_id': self.story.id}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        comment_filter = Comment.objects.filter(
            story=self.story, user=self.user).first()
        self.assertIsNotNone(comment_filter)
        self.assertEqual(comment_filter.content, 'Test Comment')

class DeleteStoryTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', email='testuser@example.com', password='testpass')
        self.story = Story.objects.create(
            title='Test Story', content='Test Content', user=self.user, date_format=1)
        self.client.login(username='testuser', password='testpass')

    def test_delete_story(self):
        url = reverse('delete-story')
        data = {'story_id': self.story.id}
        response = self.client.get(url, data)
        self.assertEqual(response.status_code, 302)
        story_filter = Story.objects.filter(id=self.story.id).first()
        self.assertIsNone(story_filter)

class SearchTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
        username='testuser', email='testuser@example.com', password='testpass')
        self.user_profile = Profile.objects.create(user=self.user)
        self.client.login(username='testuser', password='testpass')

    def test_search(self):
        url = reverse('search')
        response = self.client.get(url, {'query': 'Test Query'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'search.html')
        self.assertContains(response, 'Test Query')

class PostDetailedTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
        username='testuser', email='testuser@example.com', password='testpass')
        self.user_profile = Profile.objects.create(user=self.user)
        self.client.login(username='testuser', password='testpass')

    def test_post_detailed(self):
        story = Story.objects.create(title='Test Title', content='Test Content', user=self.user, date_format=1)
        url = reverse('postdetailed') + f'?story_id={story.id}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'postdetailed.html')
        self.assertContains(response, 'Test Title')
        self.assertContains(response, 'Test Content')

class ProfileTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
        username='testuser', email='testuser@example.com', password='testpass')
        self.user_profile = Profile.objects.create(user=self.user)
        self.client.login(username='testuser', password='testpass')

    def test_profile(self):
        user = User.objects.create_user(
        username='testuser2', email='testuser2@example.com', password='testpass')
        url = reverse('profile', args=[user.username])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profile.html')
        self.assertContains(response, user.username)

class FollowTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
        username='testuser', email='testuser@example.com', password='testpass')
        self.user_profile = Profile.objects.create(user=self.user)
        self.client.login(username='testuser', password='testpass')

    def test_follow(self):
        user = User.objects.create_user(
        username='testuser2', email='testuser2@example.com', password='testpass')
        url = reverse('follow')
        data = {'follower': self.user.username, 'user': user.username}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/profile/' + user.username)
        self.assertTrue(Follower.objects.filter(follower=self.user, user=user).exists())

class UsersFollowersTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
        username='testuser', email='testuser@example.com', password='testpass')
        self.user_profile = Profile.objects.create(user=self.user)
        self.client.login(username='testuser', password='testpass')

    def test_users_followers(self):
        user = User.objects.create_user(
        username='testuser2', email='testuser2@example.com', password='testpass')
        url = reverse('usersfollowers') + f'?user_name={user.username}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'followers.html')

class UsersFollowingTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
        username='testuser', email='testuser@example.com', password='testpass')
        self.user_profile = Profile.objects.create(user=self.user)
        self.client.login(username='testuser', password='testpass')

    def test_users_following(self):
        user = User.objects.create_user(
        username='testuser2', email='testuser2@example.com', password='testpass')
        follower1=Follower.objects.create(user=user, follower=self.user)
        url = reverse('usersfollowing') + f'?user_name={self.user.username}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertListEqual(list(response.context['followers']), [follower1])
        self.assertEqual(response.context['current_user'], self.user)

class UsersLikedTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
        username='testuser', email='testuser@example.com', password='testpass')
        self.user_profile = Profile.objects.create(user=self.user)
        self.client.login(username='testuser', password='testpass')

    def test_users_liked(self):
        story = Story.objects.create(title='Test Story', content='This is a test story.',user=self.user)
        like1 = Like.objects.create(story=story, user=self.user)
        url = reverse('usersliked') + f'?story_id={story.id}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['story'], story)
        self.assertListEqual(list(response.context['likes']), [like1])

class UsersCommentedTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
        username='testuser', email='testuser@example.com', password='testpass')
        self.user_profile = Profile.objects.create(user=self.user)
        self.client.login(username='testuser', password='testpass')

    def test_users_commented(self):
        story = Story.objects.create(title='Test Story', content='This is a test story.', user=self.user)
        comment1 = Comment.objects.create(story=story, user=self.user, content='This is a test comment.')
        url = reverse('userscommented') + f'?story_id={story.id}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['story'], story)
        self.assertListEqual(list(response.context['comments']), [comment1])

class SettingsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
        username='testuser', email='testuser@example.com', password='testpass')
        self.user_profile = Profile.objects.create(user=self.user)
        self.client.login(username='testuser', password='testpass')

    def test_settings(self):
        url = reverse('settings')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = {
        'bio': 'This is a test bio.',
        'first_name': 'Test',
        'last_name': 'User'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('index'))

        user_profile = Profile.objects.get(user=self.user)
        self.assertEqual(user_profile.bio, data['bio'])
        self.assertEqual(user_profile.first_name, data['first_name'])
        self.assertEqual(user_profile.last_name, data['last_name'])

class SignupTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_signup(self):
        url = reverse('signup')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = {
        'First Name': 'Test',
        'Last Name': 'User',
        'username': 'testuser',
        'email': 'testuser@example.com',
        'password': 'testpass',
        'password2': 'testpass'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('settings'))

        user = User.objects.get(username=data['username'])
        self.assertEqual(user.email, data['email'])
        self.assertEqual(user.first_name, data['First Name'])
        self.assertEqual(user.last_name, data['Last Name'])

        profile = Profile.objects.get(user=user)
        self.assertEqual(profile.username, data['username'])
        self.assertEqual(profile.email, data['email'])
        self.assertEqual(profile.first_name, data['First Name'])
        self.assertEqual(profile.last_name, data['Last Name'])

