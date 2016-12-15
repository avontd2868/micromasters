"""
Checks the freeze status for a final grade
"""
from django.core.cache import cache
from django.core.management import BaseCommand, CommandError

from courses.models import CourseRun
from dashboard.models import CachedEnrollment
from grades.models import FinalGradeRunInfo, FinalGrade
from grades.tasks import CACHE_ID_BASE_STR


class Command(BaseCommand):
    """
    Checks the status of the final grade freeze for
    """
    help = "Submits a celery task to freeze the final grades for all the users enrolled in a course run"

    def add_arguments(self, parser):
        parser.add_argument("course_id", help="the edx_course_key for the course run")

    def handle(self, *args, **kwargs):  # pylint: disable=unused-argument
        course_id = kwargs.get('course_id')
        try:
            run = CourseRun.objects.get(edx_course_key=course_id)
        except CourseRun.DoesNotExist:
            raise CommandError('Course Run for course_id "{0}" does not exist'.format(course_id))

        if FinalGradeRunInfo.is_course_run_complete(run):
            self.stdout.write(
                self.style.SUCCESS(
                    'Final grades for course "{0}" are complete'.format(course_id)
                )
            )
        elif FinalGradeRunInfo.is_course_run_pending(run):
            if cache.get(CACHE_ID_BASE_STR.format(course_id)):
                self.stdout.write(
                    self.style.WARNING(
                        'Final grades for course "{0}" are being processed'.format(course_id)
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        'Final grades for course "{0}" are marked as they are being processed'
                        ', but no task found.'.format(course_id)
                    )
                )
        else:
            self.stdout.write(
                self.style.WARNING(
                    'Final grades for course "{0}" are not being processed yet'.format(course_id)
                )
            )
        self.stdout.write(
            self.style.SUCCESS(
                'The students with a final grade are {0}/{1}'.format(
                    FinalGrade.objects.filter(course_run=run).count(),
                    CachedEnrollment.objects.filter(course_run=run).count(),
                )
            )
        )
