"""
Tasks for exams
"""
from datetime import datetime
import tempfile

import pytz

from exams.models import ExamProfile
from exams.pearson import (
    ccd_writer,
    upload_tsv,
)
from micromasters.celery import async


@async.task
def export_exam_profiles():
    """
    Sync any outstanding profiles
    """
    exam_profiles = ExamProfile.objects \
        .filter(status=ExamProfile.PROFILE_PENDING) \
        .select_related('profile')
    file_prefix = datetime.now(pytz.utc).strftime('ccd-%Y%m%d%H_')
    valid_profiles, invalid_profiles = [], []

    # write the file out locally
    # this will be written out to a file like: /tmp/ccd-20160405_kjfiamdf.dat
    with tempfile.NamedTemporaryFile(
        prefix=file_prefix,
        encoding='utf-8',
        suffix='.dat',
        mode='w',
    ) as tsv:
        valid_profiles, invalid_profiles = ccd_writer(exam_profiles, tsv)

        # flush data to disk before upload
        tsv.flush()

        # upload to SFTP server
        upload_tsv(tsv.name)

    # update records to reflect the successful upload
    if valid_profiles:
        exam_profile_ids = [exam_profile.id for exam_profile in valid_profiles]
        ExamProfile.objects \
            .filter(id__in=exam_profile_ids) \
            .update(status=ExamProfile.PROFILE_IN_PROGRESS)

    # update records to reflect invalid profile
    if invalid_profiles:
        exam_profile_ids = [exam_profile.id for exam_profile in invalid_profiles]
        ExamProfile.objects \
            .filter(id__in=exam_profile_ids) \
            .update(status=ExamProfile.PROFILE_INVALID)
