"""
Tasks for the course app
"""
import logging

from grades.api import freeze_course_run_grades
from micromasters.celery import async


log = logging.getLogger(__name__)


@async.task
def freeze_course_run_final_grades(course_run):
    """
    Task to freeze the final grades for a course run
    """
    try:
        freeze_course_run_grades(course_run)
    except:
        log.exception('Error while freezing final grades for course run "%s"', course_run.edx_course_key)
