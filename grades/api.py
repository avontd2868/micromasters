"""
APIs for the grades app
"""
import logging
from collections import namedtuple

from django.contrib.auth.models import User

from dashboard.api_edx_cache import CachedEdxUserData
from dashboard.models import CachedEnrollment
from grades.models import (
    FinalGrade,
    FinalGradeRunInfo,
    FinalGradeStatus,
)


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


def get_users_final_grade_freeze(course_run):
    """
    Public function to extract all the users that need a final grade freeze for a course run.
    All the users that are enrolled in a course run must have frozen final grade.

    Args:
        course_run (CourseRun): a course run model object

    Returns:
        queryset: a queryset of users
    """
    # get the list of users enrolled in the course
    users_in_cache = set(CachedEnrollment.get_cached_users(course_run))
    # get all the users with already frozen final grade
    users_already_processed = set(FinalGrade.get_frozen_users(course_run))
    return User.objects.filter(pk__in=users_in_cache.difference(users_already_processed))


def freeze_user_final_grade(user, course_run):
    """
    Public function to freeze final grades for the a user in a course run.

    Args:
        user (User): a django User
        course_run (CourseRun): a course run model object

    Returns:
        None
    """
    # no need to do anything if the course run is not ready
    if not course_run.can_freeze_grades:
        log.info(
            'the grade for user "%s" course "%s" cannot be frozen yet',
            user.username, course_run.edx_course_key
        )
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


def freeze_course_run_grades(course_run):
    """
    Freezes all the users' final grade in a course run

    Args:
        course_run (CourseRun): a course run model object

    Returns:
        None
    """
    # no need to do anything if the course run is not ready
    if not course_run.can_freeze_grades:
        log.info('the grades course "%s" cannot be frozen yet', course_run.edx_course_key)
        return

    # if it has already completed, do not do anything
    if FinalGradeRunInfo.objects.filter(course_run=course_run, status=FinalGradeStatus.COMPLETE).exists():
        return

    # create an entry in with pending status ('pending' is the default status)
    course_fg_info, _ = FinalGradeRunInfo.objects.get_or_create(course_run=course_run)

    for user in get_users_final_grade_freeze(course_run):
        freeze_user_final_grade(user, course_run)

    # if after the freeze has run for the user there are no more users to freeze, set the run as complete
    users_still_to_freeze = get_users_final_grade_freeze(course_run)
    if users_still_to_freeze.count() == 0:
        course_fg_info.staus = FinalGradeStatus.COMPLETE
        course_fg_info.save()
