"""
Factories for exams
"""
import pytz

import factory
import faker
from factory import SubFactory, LazyAttribute
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyChoice

from courses.factories import CourseFactory
from exams.models import (
    ExamAuthorization,
    ExamProfile,
)
from micromasters.factories import UserFactory
from profiles.factories import ProfileFactory

FAKE = faker.Factory.create()

class ExamProfileFactory(DjangoModelFactory):
    """
    Factory for ExamProfile
    """
    status = FuzzyChoice(
        [value[0] for value in ExamProfile.PROFILE_STATUS_CHOICES]
    )
    profile = SubFactory(ProfileFactory)

    class Meta:  # pylint: disable=missing-docstring
        model = ExamProfile

class ExamAuthorizationFactory(DjangoModelFactory):
    """
    Factory for ExamAuthorization
    """
    user = SubFactory(UserFactory)
    course = SubFactory(CourseFactory)

    operation = FuzzyChoice(
        [value[0] for value in ExamAuthorization.OPERATION_CHOICES]
    )
    status = FuzzyChoice(
        [value[0] for value in ExamAuthorization.STATUS_CHOICES]
    )
    date_first_eligible = factory.LazyAttribute(
        lambda x: FAKE.date_time_this_year(before_now=False, after_now=True, tzinfo=pytz.utc)
    )
    date_last_eligible = factory.LazyAttribute(
        lambda x: FAKE.date_time_this_year(before_now=False, after_now=True, tzinfo=pytz.utc)
    )

    class Meta:  # pylint: disable=missing-docstring
        model = ExamAuthorization
