"""
Tests for exam models
"""
from unittest import TestCase

from exams.models import ExamProfile


class ExamProfileTest(TestCase):
    """Tests for ExamProfiles"""

    def test_exam_profile_str(self):  # pylint: disable=no-self-use
        """
        Test method ExamProfile.__str__ prints correctly
        """
        ep = ExamProfile(id=1, status=ExamProfile.PROFILE_IN_PROGRESS)

        assert str(ep) == 'Exam Profile "1" with status "in-progress"'
