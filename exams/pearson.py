"""
Pearson specific exam code
"""
from functools import partial
from operator import attrgetter
import csv
import logging

from django.conf import settings
import pycountry
import pysftp

from exams.exceptions import (
    InvalidProfileDataException,
    InvalidTsvRow,
)

# custom csv dialect for Pearson
csv.register_dialect(
    'pearsontsv',
    delimiter='\t',
)

PEARSON_DATETIME_FORMAT = "%Y/%m/%d %H:%M:%S"

log = logging.getLogger(__name__)


def format_datetime(dt):
    """
    Formats a datetime to Pearson's required format
    """
    return dt.strftime(PEARSON_DATETIME_FORMAT)


def get_field_mapper(field):
    """
    Returns a field mapper, accepts either a property path in str form or a callable
    """
    if isinstance(field, str):
        return attrgetter(field)
    elif callable(field):
        return field
    else:
        raise TypeError("field_mapper must be a str or a callable")


def writer(fields, field_prefix=None):
    """
    Creates a new writer for the given field mappins
    Usage:
        test_writer = writer([
            ('OutputField1', 'prop1'),
            ...
        ])

        obj = SourceObj(prop1=1234)

        test_writer(file, [obj])
    """
    columns = [column for column, _ in fields]
    field_mappers = [(column, get_field_mapper(field)) for column, field in fields]
    prefix_mapper = attrgetter(field_prefix) if field_prefix else None

    def _map_row(row):
        if prefix_mapper:
            row = prefix_mapper(row)
        return {column: field_mapper(row) for column, field_mapper in field_mappers}

    def _writer(file, rows):
        tsv_writer = csv.DictWriter(
            file,
            columns,
            dialect='pearsontsv',
            restval='',  # ensure we don't print 'None' into the file for optional fields
        )

        tsv_writer.writeheader()

        valid_rows, invalid_rows = [], []

        for row in rows:
            try:
                tsv_writer.writerow(_map_row(row))
                valid_rows.append(row)
            except InvalidTsvRow:
                log.exception("Invalid tsv row")
                invalid_rows.append(row)

        return (valid_rows, invalid_rows)

    return _writer


def optional_field(field, value):
    """
    Returns value if it is not None, otherwise an empty string
    """
    value = get_field_mapper(field)(value)
    return value if value else ''


def profile_country_to_alpha3(profile):
    """
    Returns the alpha3 code of a profile's country
    """
    # Pearson requires ISO-3166 alpha3 codes, but we store as alpha2
    try:
        country = pycountry.countries.get(alpha_2=profile.country)
    except KeyError:
        raise InvalidProfileDataException()
    return country.alpha_3


ccd_writer = writer([
    ('ClientCandidateId', 'student_id'),
    ('FirstName', 'romanized_first_name'),
    ('LastName', 'romanized_last_name'),
    ('Email', 'user.email'),
    ('Address1', 'address1'),
    ('Address2', partial(optional_field, 'address2')),
    ('Address3', partial(optional_field, 'address3')),
    ('City', 'city'),
    ('State', 'state_or_territory'),
    ('PostalCode', 'postal_code'),
    ('Country', profile_country_to_alpha3),
    ('Phone', 'phone_number'),
    ('PhoneCountryCode', 'phone_country_code'),
    ('LastUpdate', lambda profile: format_datetime(profile.updated_on)),
], field_prefix='profile')


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
