"""
Tasks for exams
"""
from datetime import datetime
import tempfile

import pytz

from exams.models import (
    ExamAuthorization,
    ExamProfile,
)
from exams.pearson import (
    upload_tsv,
    write_cdd_file,
    write_ead_file,
)
from micromasters.celery import async
from profiles.models import Profile


@async.task
def export_exam_profiles():
    """
    Sync any outstanding profiles
    """
    exam_profiles = (ExamProfile.objects
                     .filter(status=ExamProfile.PROFILE_PENDING)
                     .select_related('profile'))
    file_prefix = datetime.now(pytz.utc).strftime('cdd-%Y%m%d%H_')
    valid_profiles, invalid_profiles = [], []

    # write the file out locally
    # this will be written out to a file like: /tmp/ccd-20160405_kjfiamdf.dat
    with tempfile.NamedTemporaryFile(
        prefix=file_prefix,
        encoding='utf-8',
        suffix='.dat',
        mode='w',
    ) as tsv:
        valid_profiles, invalid_profiles = write_cdd_file(exam_profiles, tsv)

        # flush data to disk before upload
        tsv.flush()

        # upload to SFTP server
        upload_tsv(tsv.name)

    # update records to reflect the successful upload
    if valid_profiles:
        exam_profile_ids = [exam_profile.id for exam_profile in valid_profiles]
        (ExamProfile.objects
         .filter(id__in=exam_profile_ids)
         .update(status=ExamProfile.PROFILE_IN_PROGRESS))

    # update records to reflect invalid profile
    if invalid_profiles:
        exam_profile_ids = [exam_profile.id for exam_profile in invalid_profiles]
        (ExamProfile.objects
         .filter(id__in=exam_profile_ids)
         .update(status=ExamProfile.PROFILE_INVALID))



@async.task
def export_exam_authorizations():
    """
    Sync any outstanding profiles
    """
    exam_authorizations = (ExamAuthorization.objects
                           .filter(status=ExamAuthorization.STATUS_PENDING)
                           .prefetch_related('user__profile', 'course__program'))
    file_prefix = datetime.now(pytz.utc).strftime('ead-%Y%m%d%H_')
    valid_auths, invalid_auths = [], []

    # write the file out locally
    # this will be written out to a file like: /tmp/ead-20160405_kjfiamdf.dat
    with tempfile.NamedTemporaryFile(
        prefix=file_prefix,
        encoding='utf-8',
        suffix='.dat',
        mode='w',
    ) as tsv:
        valid_auths, _ = write_ead_file(tsv, exam_authorizations)

        # flush data to disk before upload
        tsv.flush()

        # upload to SFTP server
        upload_tsv(tsv.name)

    # update records to reflect the successful upload
    if valid_auths:
        exam_auth_ids = [exam_auth.id for exam_auth in valid_auths]
        (ExamProfile.objects
         .filter(id__in=exam_auth_ids)
         .update(status=ExamAuthorization.STATUS_IN_PROGRESS))
