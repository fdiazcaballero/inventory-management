from django.urls import path
from rest_framework.test import APITestCase, URLPatternsTestCase
from rest_framework import status
from nory_project.urls import ping
from rest_framework.test import APIClient


class PingTests(APITestCase, URLPatternsTestCase):
    '''
    This class is for demonstrations purposes and to have already
    simple test in place to use in the pre-commit hooks and build pipelines.
    For the new services forking the skeleton please add unit tests accordinly
    to your business logic.
    Some places to look for examples and learning are:
    https://www.django-rest-framework.org/api-guide/testing/
    https://docs.djangoproject.com/en/4.1/topics/testing/overview/
    '''
    urlpatterns = [
        path('ping/', ping, name='ping'),
    ]

    def test_ping(self):
        client = APIClient()
        response = client.get('/ping/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
