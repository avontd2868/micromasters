"""
APIs for the grades app
"""
from dashboard.api_edx_cache import CachedEdxUserData


def _compute_grade_for_fa(user_edx_run_data):
    """
    Gets the final grade for an user enrolled in the
    course run that is part of a financial aid program.
    """


def _compute_grade_for_non_fa(user_edx_run_data):
    """
    Gets the final grade for an user enrolled in the
    course run that is part of a non financial aid program.
    If the user has a certificate, she has passed otherwise she has not.

    Args:
        user_edx_run_data (User): a django User

    Returns:
        tuple: a tuple of (float, bool) representing the final grade
            of the user in the course run and whether she passed it
    """



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
        tuple: a tuple of (float, bool) representing the final grade
            of the user in the course run and whether she passed it
    """
    # no need to do anything if the course run is not ready
    if not course_run.can_freeze_grades:
        return
    # pull the cached data for the user
    user_data = CachedEdxUserData(user, course_run.course.program)
    run_data = user_data.get_run_data(course_run.edx_course_key)

    # pick the right function
    final_grade_func = _get_compute_func(course_run)
    return final_grade_func(run_data)
