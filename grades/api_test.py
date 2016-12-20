"""
Tests for grades API
"""
from unittest.mock import patch, MagicMock, ANY

from backends.edxorg import EdxOrgOAuth2
from courses.factories import CourseRunFactory
from dashboard.api_edx_cache import CachedEdxUserData, UserCachedRunData
from dashboard.factories import (
    CachedCertificateFactory,
    CachedCurrentGradeFactory,
    CachedEnrollmentFactory,
)
from grades import api
from micromasters.factories import UserFactory
from search.base import ESTestCase


# pylint: disable=no-self-use, protected-access


class FinalGradeFuncsTests(ESTestCase):
    """
    Tests for final grades functions
    """

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory.create()
        cls.user.social_auth.create(
            provider=EdxOrgOAuth2.name,
            uid="{}_edx".format(cls.user.username),
            extra_data={"access_token": "fooooootoken"}
        )

        cls.course_run1 = CourseRunFactory.create()
        cls.course_run1.course.program.financial_aid_availability = True
        cls.course_run2 = CourseRunFactory.create()
        cls.course_run2.course.program = cls.course_run1.course.program

        cls.course_run3 = CourseRunFactory.create()
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
