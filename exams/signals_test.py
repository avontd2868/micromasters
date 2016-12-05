"""
Tests for exam signals
"""

from unittest import TestCase
from unittest.mock import patch

from exams.factories import ExamProfileFactory
from profiles.factories import ProfileFactory

class ExamSignalsTest(TestCase):
    @patch('exams.signals.update_exam_profile.send')
    def test_update_exam_profile_called(self, mock):
        profile = ProfileFactory.create()
        profile_exam = ProfileExamFactory.create(profile=profile)
        profile.first_name = 'NewName'
        profile.save()

        self.assertEqual(mock.call_count, 1)



