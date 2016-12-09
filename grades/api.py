"""
APIs for the grades app
"""
from dashboard.api_edx_cache import CachedEdxUserData


def compute_grade_for_fa(user, course_run):
    """
    Gets the final grade for an user enrolled in the
    course run that is part of a financial aid program.
    """


def compute_grade_for_non_fa(user, course_run):
    """
    Gets the final grade for an user enrolled in the
    course run that is part of a non financial aid program.
    """


def get_compute_func(course_run):
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
    return compute_grade_for_fa if course_run.course.program.financial_aid_availability else compute_grade_for_non_fa


def get_final_grade(user, course_run):
    """
    Computers the final grade for an user in a course run
    """
    # no need to do anything if the course run is not ready
    if not course_run.can_freeze_grades:
        return
    # pull the cached data for the user
    user_data = CachedEdxUserData(user, course_run.course.program)
    run_data = user_data.get_run_data(course_run.edx_course_key)
