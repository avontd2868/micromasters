"""
Test cases for course utils
"""
from datetime import datetime
from django.test import TestCase
from courses.utils import (
    get_year_season_from_course_run
)
from courses.factories import CourseRunFactory


class CourseUtilTests(TestCase):
    """
    Test cases for course utils
    """

    def test_get_year_season_from_course_run(self):  # pylint: disable=no-self-use
        """
        Tests that year/season is calculated appropriately from a CourseRun
        """
        fall_2016_dt = datetime.strptime('10/01/2016', "%m/%d/%Y")
        test_run1 = CourseRunFactory.build(edx_course_key='course-v1:MITx+CTL.SC0x+1T2016', start_date=fall_2016_dt)
        test_run2 = CourseRunFactory.build(edx_course_key='MITx/14.73x_1/1T2016', start_date=fall_2016_dt)
        test_run3 = CourseRunFactory.build(start_date=fall_2016_dt, edx_course_key='invalid')
        assert get_year_season_from_course_run(test_run1) == (2016, 'Spring')
        assert get_year_season_from_course_run(test_run2) == (2016, 'Spring')
        assert get_year_season_from_course_run(test_run3) == (2016, 'Fall')
