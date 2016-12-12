"""
APIs for the grades app
"""
import logging
from collections import namedtuple

from dashboard.api_edx_cache import CachedEdxUserData
from grades.models import FinalGrade, FinalGradeStatus


log = logging.getLogger(__name__)

UserFinalGrade = namedtuple('UserFinalGrade', ['grade', 'passed'])


def _compute_grade_for_fa(user_edx_run_data):
    """
    Gets the final grade for an user enrolled in the course run that is part of a financial aid program.

    Args:
        user_edx_run_data (dashboard.api_edx_cache.UserCachedRunData): the edx cached data for an user in a course run

    Returns:
        UserFinalGrade: a namedtuple of (float, bool,) representing the final grade
            of the user in the course run and whether she passed it
    """
    run_passed = None
    grade = None
    if user_edx_run_data.certificate is not None:
        run_passed = True
        grade = user_edx_run_data.certificate.grade
    else:
        run_passed = user_edx_run_data.current_grade.passed
        grade = user_edx_run_data.current_grade.percent
    return UserFinalGrade(grade=grade, passed=run_passed)


def _compute_grade_for_non_fa(user_edx_run_data):
    """
    Gets the final grade for an user enrolled in the
    course run that is part of a non financial aid program.
    If the user has a certificate, she has passed otherwise she has not.

    Args:
        user_edx_run_data (dashboard.api_edx_cache.UserCachedRunData): the edx cached data for an user in a course run

    Returns:
        UserFinalGrade: a namedtuple of (float, bool,) representing the final grade
            of the user in the course run and whether she passed it
    """
    run_passed = user_edx_run_data.certificate is not None
    grade = user_edx_run_data.certificate.grade if run_passed else user_edx_run_data.current_grade.percent
    return UserFinalGrade(grade=grade, passed=run_passed)


def _get_compute_func(course_run):
    """
    Gets the proper function to compute the final grade.

    Currently this implements a very simple logic, but it seems that
    in the near future we could have policies to compute the final grade
    that can be different per program (run?).

    Args:
        course_run (CourseRun): a course run model object

    Returns:
        function: a function to be called to compute the final grade
    """
    return _compute_grade_for_fa if course_run.course.program.financial_aid_availability else _compute_grade_for_non_fa


def get_final_grade(user, course_run):
    """
    Public function to compute final grades for the a user in a course run.

    Args:
        user (User): a django User
        course_run (CourseRun): a course run model object

    Returns:
        UserFinalGrade: a namedtuple of (grade, passed,) representing the final grade
            of the user in the course run and whether she passed it
    """
    # pull the cached data for the user
    user_data = CachedEdxUserData(user, course_run.course.program)
    run_data = user_data.get_run_data(course_run.edx_course_key)

    # pick the right function
    final_grade_func = _get_compute_func(course_run)
    return final_grade_func(run_data)


def freeze_final_grade(user, course_run):
    """
    Public function to compute final grades for the a user in a course run.

    Args:
        user (User): a django User
        course_run (CourseRun): a course run model object

    Returns:
        None
    """
    # no need to do anything if the course run is not ready
    if not course_run.can_freeze_grades:
        return
    try:
        final_grade = get_final_grade(user, course_run)
    except:
        log.exception('Impossible to freeze final grade for user "{0}"'.format(user.username))
        return
    FinalGrade.objects.create(
        user=user,
        course_run=course_run,
        grade=final_grade.grade,
        passed=final_grade.passed,
        status=FinalGradeStatus.COMPLETE
    )
