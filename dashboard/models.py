"""
Models for dashboard
"""

from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from django.db.models import (
    DateTimeField,
    ForeignKey,
    Model,
    OneToOneField,
)
from edx_api.certificates import (
    Certificate,
    Certificates,
)
from edx_api.enrollments import Enrollments
from edx_api.grades import (
    CurrentGrade,
    CurrentGrades
)

from courses.models import CourseRun, Program


class CachedEdxInfoModel(Model):
    """
    Base class to define other cached models
    """
    user = ForeignKey(User)
    course_run = ForeignKey(CourseRun)
    data = JSONField()

    class Meta:
        unique_together = (('user', 'course_run'), )
        abstract = True

    @classmethod
    def active_qset_all(cls, user):
        """
        Returns a queryset for the active records associated with a User

        Args:
            user (User): an User object

        Returns:
            QuerySet: a queryset of all the elements for the provided user
        """
        return cls.objects.filter(user=user)

    @classmethod
    def active_qset_program(cls, user, program):
        """
        Returns a queryset for the active records associated with a User/Program pair

        Args:
            user (User): an User object
            program (courses.models.Program): a program

        Returns:
            QuerySet: a queryset of all the elements for the provided user and program
        """
        return cls.objects.filter(
            user=user,
            course_run__course__program=program
        )

    @classmethod
    def active_data(cls, user, program):
        """
        Returns a list containing the 'data' property of every active record associated
        with a User/Program pair

        Args:
            user (User): an User object
            program (courses.models.Program): a program

        Returns:
            QuerySet: a queryset of all the data fields for the provided user and program
        """
        return cls.active_qset_program(user, program).values_list('data', flat=True).all()

    @classmethod
    def active_course_ids(cls, user):
        """
        Returns a list of all the Course IDs for the cached data

        Args:
            user (User): an User object

        Returns:
            list: a list of all the course key fields for the provided user
        """
        return list(cls.active_qset_all(user).values_list('course_run__edx_course_key', flat=True).all())

    @classmethod
    def delete_all_but(cls, user, course_ids_list):
        """
        Given an user, deletes all her object in the cache but the provided course ids

        Args:
            user (User): an User object
            course_ids_list (list): a list of course IDs to NOT be deleted

        Returns:
            None
        """
        cls.active_qset_all(user).exclude(course_run__edx_course_key__in=course_ids_list).delete()

    @classmethod
    def get_edx_data(cls, user):
        """
        Method to retrieve the cached date and encapsulate in specific edx-api-client classes.
        Needs to be implemented in a per cache type bases
        """
        raise NotImplementedError

    def __str__(self):
        """
        String representation of the model object
        """
        return 'user "{0}", run "{1}"'.format(
            self.user.username,
            self.course_run.edx_course_key,
        )


class CachedEnrollment(CachedEdxInfoModel):
    """
    Model for user enrollment data from edX
    """

    @classmethod
    def get_edx_data(cls, user):
        """
        Implementation for enrollments.

        Args:
            user (User): an User object

        Returns:
            Enrollments: an enrollments object for the user
        """
        return Enrollments(
            [enrollment.data for enrollment in cls.active_qset_all(user)]
        )

    @classmethod
    def active_data(cls, user, program):
        """
        Returns a list containing the 'data' property of every active record associated
        with a User/Program pair

        Args:
            user (User): an User object
            program (courses.models.Program): a program

        Returns:
            QuerySet: a queryset of all the data fields for the provided user and program
        """
        qset = cls.active_qset_program(user, program)
        values = qset.values_list('data', 'course_run__title').all()
        return [{ **data, **{ 'title': title }} for (data, title) in values]


class CachedCertificate(CachedEdxInfoModel):
    """
    Model for certificate data from edX
    """
    @classmethod
    def get_edx_data(cls, user):
        """
        Implementation for certificates.

        Args:
            user (User): an User object

        Returns:
            Certificates: a certificates object for the user
        """
        return Certificates([
            Certificate(certificate.data) for certificate in cls.active_qset_all(user)
        ])



class CachedCurrentGrade(CachedEdxInfoModel):
    """
    Model for current grade data from edX
    """
    @classmethod
    def get_edx_data(cls, user):
        """
        Implementation for current grades.

        Args:
            user (User): an User object

        Returns:
            CurrentGrades: a current grades object for the user
        """
        return CurrentGrades([
            CurrentGrade(grade.data) for grade in cls.active_qset_all(user)
        ])


class UserCacheRefreshTime(Model):
    """
    Model to store the last refresh timestamp for each of the edX cached info model.
    """
    user = OneToOneField(User)
    enrollment = DateTimeField(null=True)
    certificate = DateTimeField(null=True)
    current_grade = DateTimeField(null=True)

    def __str__(self):
        """
        String representation of the model object
        """
        return 'user "{0}"'.format(self.user.username)


class ProgramEnrollment(Model):
    """
    Model for student enrollments in Programs
    """
    user = ForeignKey(User)
    program = ForeignKey(Program)

    class Meta:
        unique_together = (('user', 'program'), )

    @classmethod
    def prefetched_qset(cls):
        """
        Returns a queryset that will prefetch Program and User (with Profile)
        """
        return cls.objects.select_related('user__profile', 'program')

    def __str__(self):
        """
        String representation of the model object
        """
        return 'user "{0}" enrolled in program "{1}"'.format(
            self.user.username,
            self.program.title
        )
