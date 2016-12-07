"""
Factories for exams
"""
from factory import SubFactory
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyChoice

from exams.models import ExamProfile
from profiles.factories import ProfileFactory


class ExamProfileFactory(DjangoModelFactory):
    """
    Factory for ExamProfile
    """
    status = FuzzyChoice(
        [value[0] for value in ExamProfile.PROFILE_STATUS_CHOICES]
    )
    profile = SubFactory(ProfileFactory)

    class Meta:
        model = ExamProfile
