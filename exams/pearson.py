"""
Pearson specific exam code
"""
import csv
import logging

from django.conf import settings
import pycountry
import pysftp

from exams.exceptions import InvalidProfileDataException

# custom csv dialect for Pearson
csv.register_dialect(
    'pearsontsv',
    delimiter='\t',
)

CCD_FIELD_NAMES = [
    'ClientCandidateId',
    'FirstName',
    'LastName',
    'Email',
    'Address1',
    'Address2',
    'Address3',
    'City',
    'State',
    'PostalCode',
    'Country',
    'Phone',
    'PhoneCountryCode',
    'LastUpdate',
]

LAST_UPDATE_FORMAT = "%Y-%m-%d %H:%M:%S"


log = logging.getLogger(__name__)


def profile_to_ccd_row(profile):
    """
    Converts a Profile to a dictionary representing the TSV row
    """
    # Pearson requires ISO-3166 alpha3 codes, but we store as alpha2
    try:
        country = pycountry.countries.get(alpha_2=profile.country)
    except KeyError:
        raise InvalidProfileDataException()
    row = {
        'ClientCandidateId': profile.student_id,
        'FirstName': profile.romanized_first_name,
        'LastName': profile.romanized_last_name,
        'Email': profile.user.email,
        'Address1': profile.address1,
        'City': profile.city,
        'State': profile.state_or_territory,
        'PostalCode': profile.postal_code,
        'Country': country.alpha_3,
        'Phone': profile.phone_number,
        'PhoneCountryCode': profile.phone_country_code,
        'LastUpdate': profile.updated_on.strftime(LAST_UPDATE_FORMAT),
    }

    if profile.address2:
        row['Address2'] = profile.address2
    if profile.address3:
        row['Address3'] = profile.address3

    return row


def write_profiles_ccd(profiles, tsv_file):
    """
    Writes profiles to a tsv file using Pearson's CCD format
    """
    writer = csv.DictWriter(
        tsv_file,
        CCD_FIELD_NAMES,
        dialect='pearsontsv',
        restval='',  # ensure we don't print 'None' into the file for optional fields
    )

    writer.writeheader()

    for profile in profiles:
        try:
            writer.writerow(profile_to_ccd_row(profile))
        except InvalidProfileDataException:
            log.exception(
                "Invalid country %s for user %s",
                profile.country,
                profile.user.id
            )


def upload_tsv(file_path):
    """
    Upload the given TSV files to the remote
    """
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None  # ignore knownhosts
    with pysftp.Connection(
        host=str(settings.EXAMS_SFTP_HOST),
        port=int(settings.EXAMS_SFTP_PORT),
        username=str(settings.EXAMS_SFTP_USERNAME),
        password=str(settings.EXAMS_SFTP_PASSWORD),
        cnopts=cnopts,
    ) as sftp:
        with sftp.cd(str(settings.EXAMS_SFTP_UPLOAD_DIR)):
            sftp.put(file_path)
