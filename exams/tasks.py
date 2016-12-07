"""
Tasks for exams
"""
from datetime import datetime

import os
import pytz
import tempfile


from exams.models import ExamProfile
from exams.pearson import (
    write_profiles_ccd,
    upload_tsv,
)
from micromasters.celery import async


@async.task
def export_exam_profiles():
    """
    Sync any outstanding profiles
    """
    exam_profiles = ExamProfile.objects.filter(status=ExamProfile.PROFILE_PENDING)
    file_prefix = datetime.now(pytz.utc).strftime('ccd-%Y%m%d%H_')

    # write the file out locally
    # this will be written out to a file like: /tmp/ccd-20160405_kjfiamdf.dat
    with tempfile.NamedTemporaryFile(
        prefix=file_prefix,
        suffix='.dat',
    ) as tsv:
        write_profiles_ccd(exam_profiles, tsv)

        # flush data to disk before upload
        tsv.flush()

        # upload to SFTP server
        upload_tsv(tsv.name)

    # update records to reflect the successful upload
    exam_profiles.update(status=ExamProfile.PROFILE_IN_PROGRESS)
