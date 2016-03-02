"""
Test end to end django views.
"""
from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse


class TestViews(TestCase):
    """
    Test that the views work as expected.
    """
    def setUp(self):
        """Common test setup"""
        super(TestViews, self).setUp()
        self.client = Client()

    def test_index_view(self):
        """Verify the index view is as expected"""
        response = self.client.get(reverse('ui_index'))
        self.assertContains(
            response,
            "Hi, I'm ui",
            status_code=200
        )
