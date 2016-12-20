"""
Tests for grades API
"""
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, ANY

import pytz
from django.core.exceptions import ImproperlyConfigured

from backends.edxorg import EdxOrgOAuth2
from courses.factories import CourseRunFactory
from dashboard.api_edx_cache import CachedEdxUserData, UserCachedRunData
from dashboard.factories import (
    CachedCertificateFactory,
    CachedCurrentGradeFactory,
    CachedEnrollmentFactory,
)
from grades import api
from grades.models import FinalGrade, FinalGradeStatus
from micromasters.factories import UserFactory
from search.base import ESTestCase


# pylint: disable=no-self-use, protected-access


class GradeAPITests(ESTestCase):
    """
    Tests for final grades api
    """

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory.create()
        cls.user.social_auth.create(
            provider=EdxOrgOAuth2.name,
            uid="{}_edx".format(cls.user.username),
            extra_data={"access_token": "fooooootoken"}
        )

        cls.course_run1 = CourseRunFactory.create(freeze_grade_date=datetime.now(tz=pytz.UTC)-timedelta(days=1))
        cls.course_run1.course.program.financial_aid_availability = True
        cls.course_run2 = CourseRunFactory.create(freeze_grade_date=None)
        cls.course_run2.course.program = cls.course_run1.course.program

        cls.course_run3 = CourseRunFactory.create(freeze_grade_date=datetime.now(tz=pytz.UTC)+timedelta(days=1))
        cls.course_run3.course.program.financial_aid_availability = False
        cls.course_run4 = CourseRunFactory.create()
        cls.course_run4.course.program = cls.course_run3.course.program

        all_course_runs = (cls.course_run1, cls.course_run2, cls.course_run3, cls.course_run4, )

        cls.enrollments = {
            course_run.edx_course_key: CachedEnrollmentFactory.create(
                user=cls.user, course_run=course_run) for course_run in all_course_runs
        }

        cls.current_grades = {
            course_run.edx_course_key: CachedCurrentGradeFactory.create(
                user=cls.user, course_run=course_run) for course_run in all_course_runs
        }

        cls.certificates = {
            course_run.edx_course_key: CachedCertificateFactory.create(
                user=cls.user, course_run=course_run) for course_run in (cls.course_run2, cls.course_run4)
        }

        cls.user_edx_data = CachedEdxUserData(cls.user)

    def test_compute_grade_for_fa(self):
        """
        Tests for _compute_grade_for_fa function
        """
        run1_data = self.user_edx_data.get_run_data(self.course_run1.edx_course_key)
        run2_data = self.user_edx_data.get_run_data(self.course_run2.edx_course_key)

        grade1_from_cur_grade = api._compute_grade_for_fa(run1_data)
        grade2_from_cert = api._compute_grade_for_fa(run2_data)

        assert isinstance(grade1_from_cur_grade, api.UserFinalGrade)
        assert isinstance(grade2_from_cert, api.UserFinalGrade)

        assert grade1_from_cur_grade.passed == self.current_grades.get(
            self.course_run1.edx_course_key).data.get('passed')
        assert grade1_from_cur_grade.grade == self.current_grades.get(
            self.course_run1.edx_course_key).data.get('percent')

        assert grade2_from_cert.passed is True
        assert grade2_from_cert.grade == self.certificates.get(
            self.course_run2.edx_course_key).data.get('grade')

    def test_compute_grade_for_non_fa(self):
        """
        Tests for _compute_grade_for_non_fa function
        """
        run3_data = self.user_edx_data.get_run_data(self.course_run3.edx_course_key)
        run4_data = self.user_edx_data.get_run_data(self.course_run4.edx_course_key)

        grade3 = api._compute_grade_for_non_fa(run3_data)
        grade4 = api._compute_grade_for_non_fa(run4_data)

        assert isinstance(grade3, api.UserFinalGrade)
        assert isinstance(grade4, api.UserFinalGrade)

        assert grade3.passed is False
        assert grade3.grade == self.current_grades.get(
            self.course_run3.edx_course_key).data.get('percent')
        assert grade4.passed is True
        assert grade4.grade == self.certificates.get(
            self.course_run4.edx_course_key).data.get('grade')

    def test_get_compute_func(self):
        """
        tests for _get_compute_func function
        """
        assert api._get_compute_func(self.course_run1) == api._compute_grade_for_fa
        assert api._get_compute_func(self.course_run3) == api._compute_grade_for_non_fa

    @patch('dashboard.api_edx_cache.CachedEdxDataApi.update_cached_current_grades', new_callable=MagicMock)
    @patch('dashboard.api_edx_cache.CachedEdxDataApi.update_cached_certificates', new_callable=MagicMock)
    @patch('dashboard.api_edx_cache.CachedEdxDataApi.update_cached_enrollments', new_callable=MagicMock)
    @patch('backends.utils.refresh_user_token', autospec=True)
    def test_refresh_cache_final_grade(self, refr, enr, cert, grades):
        """
        tests for _refresh_cache_final_grade function
        """
        api._refresh_cache_final_grade(self.user)
        refr.assert_called_once_with(self.user.social_auth.get(provider=EdxOrgOAuth2.name))
        enr.assert_not_called()
        cert.assert_called_once_with(self.user, ANY)
        grades.assert_called_once_with(self.user, ANY)

    @patch('grades.api._compute_grade_for_non_fa', autospec=True)
    @patch('grades.api._compute_grade_for_fa', autospec=True)
    def test_get_final_grade(self, fa, non_fa):
        """
        tests for get_final_grade function
        """
        cruns = (self.course_run1, self.course_run3,)

        for crun in cruns:
            api.get_final_grade(self.user, crun)

        assert fa.called is True
        assert fa.call_count == 1
        call_arg = fa.call_args_list[0][0][0]
        assert isinstance(call_arg, UserCachedRunData)
        assert call_arg.edx_course_key == self.course_run1.edx_course_key

        assert non_fa.called is True
        assert non_fa.call_count == 1
        call_arg = non_fa.call_args_list[0][0][0]
        assert isinstance(call_arg, UserCachedRunData)
        assert call_arg.edx_course_key == self.course_run3.edx_course_key

    def test_get_users_final_grade_freeze(self):
        """
        tests for get_users_final_grade_freeze function
        """
        assert list(api.get_users_final_grade_freeze(self.course_run1)) == [self.user]

        # create another user and enrollment
        other_user = UserFactory.create()
        CachedEnrollmentFactory.create(user=other_user, course_run=self.course_run1)
        assert list(api.get_users_final_grade_freeze(self.course_run1)) == [self.user, other_user]

        # add the user to the FinalGrade model as in progress
        fg_status = FinalGrade.objects.create(
            user=other_user, course_run=self.course_run1, status=FinalGradeStatus.PENDING, grade=0.0)
        assert list(api.get_users_final_grade_freeze(self.course_run1)) == [self.user, other_user]

        # change the final grade status to complete
        fg_status.status = FinalGradeStatus.COMPLETE
        fg_status.save()
        assert list(api.get_users_final_grade_freeze(self.course_run1)) == [self.user]

    @patch('grades.api.get_final_grade', autospec=True)
    @patch('grades.api._refresh_cache_final_grade', autospec=True)
    def test_freeze_user_final_grade_error1(self, mock_refr, mock_get_fg):
        """
        Test for freeze_user_final_grade function in case of problems with can_freeze_grades
        """
        # case not ready to be frozen
        api.freeze_user_final_grade(self.user, self.course_run3)
        assert mock_refr.called is False
        assert mock_get_fg.called is False
        assert FinalGrade.objects.filter(user=self.user, course_run=self.course_run3).exists() is False

        # case without freeze date
        with self.assertRaises(ImproperlyConfigured):
            api.freeze_user_final_grade(self.user, self.course_run2)
        assert mock_refr.called is False
        assert mock_get_fg.called is False
        assert FinalGrade.objects.filter(user=self.user, course_run=self.course_run2).exists() is False

    @patch('grades.api.get_final_grade', autospec=True)
    @patch('grades.api._refresh_cache_final_grade', autospec=True)
    def test_freeze_user_final_grade_error2(self, mock_refr, mock_get_fg):
        """
        Test for freeze_user_final_grade function in case of problems with refresh of cache
        """
        mock_refr.side_effect = AttributeError
        api.freeze_user_final_grade(self.user, self.course_run1)
        assert mock_get_fg.called is False
        mock_refr.assert_called_once_with(self.user)
        assert FinalGrade.objects.filter(user=self.user, course_run=self.course_run1).exists() is False

    @patch('grades.api.get_final_grade', autospec=True)
    @patch('grades.api._refresh_cache_final_grade', autospec=True)
    def test_freeze_user_final_grade_error3(self, mock_refr, mock_get_fg):
        """
        Test for freeze_user_final_grade function in case of problems with getting the final grade
        """
        mock_get_fg.side_effect = AttributeError
        api.freeze_user_final_grade(self.user, self.course_run1)
        mock_refr.assert_called_once_with(self.user)
        mock_get_fg.assert_called_once_with(self.user, self.course_run1)
        assert FinalGrade.objects.filter(user=self.user, course_run=self.course_run1).exists() is False

    @patch('grades.api._refresh_cache_final_grade', autospec=True)
    def test_freeze_user_final_grade(self, mock_refr):
        """
        Test for freeze_user_final_grade function in case of problems with getting the final grade
        """
        api.freeze_user_final_grade(self.user, self.course_run1)
        mock_refr.assert_called_once_with(self.user)
        fg_qset = FinalGrade.objects.filter(user=self.user, course_run=self.course_run1)
        assert fg_qset.exists() is True
        fg_status = fg_qset.first()
        final_grade = api._compute_grade_for_fa(self.user_edx_data.get_run_data(self.course_run1.edx_course_key))
        assert fg_status.status == FinalGradeStatus.COMPLETE
        assert fg_status.user == self.user
        assert fg_status.course_run == self.course_run1
        assert fg_status.grade == final_grade.grade
        assert fg_status.passed == final_grade.passed
