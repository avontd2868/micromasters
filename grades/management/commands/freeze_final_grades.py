"""
Freezes final grades for a course
"""
from django.core.management import BaseCommand, CommandError

from courses.models import CourseRun
from grades.tasks import freeze_course_run_final_grades


class Command(BaseCommand):
    """
    Submits a celery task to freeze the final grades for all the users enrolled in a course run
    """
    help = "Submits a celery task to freeze the final grades for all the users enrolled in a course run"

    def add_arguments(self, parser):
        parser.add_argument("course_id", help="the edx_course_key for the course run")

    def handle(self, *args, **kwargs):  # pylint: disable=unused-argument
        course_id = kwargs.get('course_id')
        try:
            run = CourseRun.objects.get(edx_course_key=course_id)
        except CourseRun.DoesNotExist:
            raise CommandError('Course Run for course_id "{}" does not exist'.format(course_id))
        freeze_course_run_final_grades.delay(run)
        self.stdout.write(
            self.style.SUCCESS(
                'Successfully submitted async task to freeze final grades for course "{0}"'.format(course_id)
            )
        )
