"""
Factory for Users
"""
from django.contrib.auth.models import User
from factory import Sequence
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyText


class UserFactory(DjangoModelFactory):
    """Factory for Users"""
    username = Sequence(lambda n: "user_%d" % n)
    email = FuzzyText(suffix='@example.com')

    class Meta:  # pylint: disable=missing-docstring,no-init,too-few-public-methods,old-style-class
        model = User


class UserWithProfileFactory(UserFactory):
    """Factory for Users with Profiles"""
    def create(cls, **kwargs):
        """Create a user with a profile"""
        from profiles.factories import ProfileFactory

        user = super().create(**kwargs)

        ProfileFactory.create(user=user)

        return user

