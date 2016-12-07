"""
Signals for exams
"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from exams.models import ExamProfile
from profiles.models import Profile


@receiver(post_save, sender=Profile, dispatch_uid='update_exam_profile')
def update_exam_profile(sender, instance, **kwargs):  # pylint: disable=unused-argument
    """
    Signal handler to trigger a sync of the profile if an ExamProfile record exists for it.
    """
    ExamProfile.objects.filter(profile_id=instance.id).update(status=ExamProfile.PROFILE_PENDING)
