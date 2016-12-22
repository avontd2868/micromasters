"""
Tests for util functions
"""
from unittest import TestCase
import pytest
from django.db.models.signals import post_save
from factory.django import mute_signals

from backends.edxorg import EdxOrgOAuth2
from profiles import util
from profiles.factories import ProfileFactory


# pylint: disable=no-self-use
@pytest.mark.django_db
class UtilTests(TestCase):
    """
    Tests for util functions
    """
    def create_profile(self, **kwargs):
        """
        Create a profile and social auth
        """
        with mute_signals(post_save):
            profile = ProfileFactory.create(**kwargs)
            profile.user.social_auth.create(
                provider=EdxOrgOAuth2.name,
                uid="{}_edx".format(profile.user.username)
            )
            return profile

    def test_split_name_none(self):
        """
        None should be treated like an empty string
        """
        first_name, last_name = util.split_name(None)
        assert first_name == ""
        assert last_name == ""

    def test_split_name_empty(self):
        """
        split_name should always return two parts
        """
        first_name, last_name = util.split_name("")
        assert first_name == ""
        assert last_name == ""

    def test_split_name_one(self):
        """
        Split name should have the name as the first tuple item
        """
        first_name, last_name = util.split_name("one")
        assert first_name == "one"
        assert last_name == ""

    def test_split_name_two(self):
        """
        Split name with two names
        """
        first_name, last_name = util.split_name("two names")
        assert first_name == "two"
        assert last_name == "names"

    def test_split_name_more_than_two(self):
        """
        Split name should be limited to two names
        """
        first_name, last_name = util.split_name("three names here")
        assert first_name == "three"
        assert last_name == "names here"

    def test_profile_image_upload_uri(self):
        """
        Test for long profile image upload uris
        """

        too_long_url = '{}.jpg'.format('a' * 150)
        assert len(util.profile_image_upload_uri(None, too_long_url)) == 100

    def test_full_name(self):
        """
        test full name of user on given profile.
        """
        first = "Tester"
        last = "KK"
        profile = self.create_profile(first_name=first, last_name=last)
        assert util.full_name(profile) == "{} {}".format(first, last)

    def test_full_name_when_last_name_empty(self):
        """
        Test full name when last name is set empty on profile.
        """
        first = "Tester"
        last = ""
        profile = self.create_profile(first_name=first, last_name=last)
        assert util.full_name(profile) == first

    def test_full_name_when_first_name_empty(self):
        """
        Test full name when first name is set empty on profile.
        """
        first = ""
        last = "Tester"
        profile = self.create_profile(first_name=first, last_name=last)
        assert util.full_name(profile) == "{} {}".format(profile.user.username, last)
