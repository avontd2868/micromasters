"""
Tests for grades tasks
"""
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

import pytz
from django.core.cache import cache

from courses.factories import CourseRunFactory
from dashboard.factories import CachedEnrollmentFactory
from grades import tasks
from grades.models import (
    FinalGrade,
    FinalGradeStatus,
    FinalGradeRunInfo,
)
from micromasters.factories import UserFactory
from search.base import ESTestCase
from micromasters.utils import chunks


# pylint: disable=no-self-use, protected-access


class GradeTasksTests(ESTestCase):
    """
    Tests for final grades tasks
    """

    @classmethod
    def setUpTestData(cls):
        cls.users = [UserFactory.create() for _ in range(35)]

        freeze_date = datetime.now(tz=pytz.UTC)-timedelta(days=1)
        future_freeze_date = datetime.now(tz=pytz.UTC)+timedelta(days=1)
        cls.course_run1 = CourseRunFactory.create(freeze_grade_date=freeze_date)
        cls.course_run2 = CourseRunFactory.create(freeze_grade_date=freeze_date)
        cls.all_freezable_runs = [cls.course_run1, cls.course_run2]

        cls.course_run_future = CourseRunFactory.create(freeze_grade_date=future_freeze_date)
        cls.course_run_frozen = CourseRunFactory.create(freeze_grade_date=freeze_date)

        FinalGradeRunInfo.objects.create(course_run=cls.course_run_frozen, status=FinalGradeStatus.COMPLETE)

        for user in cls.users:
            CachedEnrollmentFactory.create(user=user, course_run=cls.course_run1)

    @patch('grades.tasks.freeze_course_run_final_grades', autospec=True)
    def test_find_course_runs_for_grade_freeze(self, mock_freeze):
        """
        Test for the find_course_runs_for_grade_freeze task
        """
        tasks.find_course_runs_for_grade_freeze.delay()

        assert mock_freeze.delay.call_count == len(self.all_freezable_runs)
        for run in self.all_freezable_runs:
            mock_freeze.delay.assert_any_call(run)

    @patch('grades.api.freeze_user_final_grade', autospec=True)
    def test_freeze_users_final_grade_async(self, mock_freeze_func):
        """
        Test for the freeze_users_final_grade_async task
        """
        tasks.freeze_users_final_grade_async.delay(self.users, self.course_run1)
        assert mock_freeze_func.call_count == len(self.users)
        for user in self.users:
            mock_freeze_func.assert_any_call(user, self.course_run1)

        # even if the function gives errors, it still completes
        mock_freeze_func.reset_mock()
        mock_freeze_func.side_effect = AttributeError

        tasks.freeze_users_final_grade_async.delay(self.users, self.course_run1)
        assert mock_freeze_func.call_count == len(self.users)
        for user in self.users:
            mock_freeze_func.assert_any_call(user, self.course_run1)

    def test_freeze_course_run_final_grades_1(self):
        """
        Test for the test_freeze_course_run_final_grades
        task in case it ends because the run cannot be frozen
        """
        tasks.freeze_course_run_final_grades.delay(self.course_run_future)
        # in this case there is not even an entry in the Table
        assert FinalGradeRunInfo.objects.filter(course_run=self.course_run_future).exists() is False

    def test_freeze_course_run_final_grades_2(self):
        """
        Test for the test_freeze_course_run_final_grades
        task in case it ends because the run has already been frozen
        """
        tasks.freeze_course_run_final_grades.delay(self.course_run_frozen)
        # in this case no task has started
        assert cache.get(tasks.CACHE_ID_BASE_STR.format(self.course_run_frozen.edx_course_key)) is None

    def test_freeze_course_run_final_grades_3(self):
        """
        Test for the test_freeze_course_run_final_grades
        task in case there are no more users to be processed
        """
        run_grade_info_qset = FinalGradeRunInfo.objects.filter(course_run=self.course_run2)
        assert run_grade_info_qset.exists() is False
        tasks.freeze_course_run_final_grades.delay(self.course_run2)
        assert run_grade_info_qset.exists() is True
        info_run = run_grade_info_qset.first()
        assert info_run.course_run == self.course_run2
        assert info_run.status == FinalGradeStatus.COMPLETE

    def test_freeze_course_run_final_grades_4(self):
        """
        Test for the test_freeze_course_run_final_grades
        task in case there are users to be processed
        """
        class PickableMock(MagicMock):
            """Subclass of MagicMock to be used for celery tasks"""
            def __reduce__(self):
                return (MagicMock, ())

        # first call
        run_grade_info_qset = FinalGradeRunInfo.objects.filter(course_run=self.course_run1)
        assert run_grade_info_qset.exists() is False
        with patch('grades.tasks.freeze_users_final_grade_async', new_callable=PickableMock) as freeze_task:
            tasks.freeze_course_run_final_grades.delay(self.course_run1)
        assert run_grade_info_qset.exists() is True
        info_run = run_grade_info_qset.first()
        assert info_run.course_run == self.course_run1
        assert info_run.status == FinalGradeStatus.PENDING
        cache_id = tasks.CACHE_ID_BASE_STR.format(self.course_run1.edx_course_key)
        cached_celery_task_id_1 = cache.get(cache_id)
        assert cached_celery_task_id_1 is not None
        assert freeze_task.s.call_count == 2
        for group in chunks(self.users, 20):
            freeze_task.s.assert_any_call(group, self.course_run1)

        # simulate successful freeze for most users
        successful_users = self.users[5:]
        for user in successful_users:
            FinalGrade.objects.create(
                user=user,
                grade=0.6,
                passed=True,
                course_run=self.course_run1,
                status=FinalGradeStatus.COMPLETE
            )

        # new call will process all the remaining users
        with patch('grades.tasks.freeze_users_final_grade_async', new_callable=PickableMock) as freeze_task:
            tasks.freeze_course_run_final_grades.delay(self.course_run1)
        info_run.refresh_from_db()
        assert info_run.status == FinalGradeStatus.PENDING
        cached_celery_task_id_2 = cache.get(cache_id)
        assert cached_celery_task_id_2 is not None
        assert cached_celery_task_id_2 != cached_celery_task_id_1
        freeze_task.s.assert_called_once_with(self.users[:5], self.course_run1)