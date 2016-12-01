"""
Tasks for exams
"""
import os
import pysftp

from micromasters.celery import async

from exams.models import ExamProfile
from exams.pearson import write_profiles_ccd


@async.task
def export_exam_profiles():
    """
    Sync any outstanding profiles
    """
    exam_profiles = ExamProfile.objects.filter(status=ExamProfile.PROFILE_PENDING)
    now = datetime.utcnow()
    file_path = now.strftime('/tmp/ccd-%Y-%m-%d-%H.dat')

    # write the file out locally
    with open(file_path, 'w') as tsv:
        write_profiles_ccd(profiles, tsv)

    # upload to SFTP server
    with pysftp.Connection(
            settings.EXAMS_SFTP_HOST,
            settings.EXAMS_SFTP_USERNAME,
            settings.EXAMS_SFTP_PASSWORD) as sftp:
        with sftp.cd(EXAMS_SFTP_PUT_DIR):
            sftp.put(file_path)

    # update records to reflect the successful upload
    exam_profiles.update(status=ExamProfile.PROFILE_IN_PROGRESS)

    # cleanup
    os.remove(file_path)


