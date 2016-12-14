"""
Pearson specific exam code
"""
from operator import attrgetter
import csv
import logging

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
import pycountry
import pysftp

from exams.exceptions import (
    InvalidProfileDataException,
    InvalidTsvRow,
)

PEARSON_CSV_DIALECT = 'pearsontsv'

# custom csv dialect for Pearson
csv.register_dialect(
    PEARSON_CSV_DIALECT,
    delimiter='\t',
)

PEARSON_DATETIME_FORMAT = "%Y/%m/%d %H:%M:%S"

log = logging.getLogger(__name__)


def _format_datetime(dt):
    """
    Formats a datetime to Pearson's required format
    """
    return dt.strftime(PEARSON_DATETIME_FORMAT)


def _get_field_mapper(field):
    """
    Returns a field mapper, accepts either a property path in str form or a callable
    """
    if isinstance(field, str):
        return attrgetter(field)
    elif callable(field):
        return field
    else:
        raise TypeError("field_mapper must be a str or a callable")


def _tsv_writer(fields, field_prefix=None):
    """
    Creates a new writer for the given field mappings

    The first value of the fields tuple is the destination field name.
    The second value is a str property path (e.g. "one.two.three") or
    a callable that when passed a row returns a computed field value

    Arguments:
        fields (List): list of (str, str|callable) tuples
        field_prefix (str): path prefix to prefix field lookups with

    Examples:
        test_writer = writer([
            ('OutputField1', 'prop1'),
            ...
        ], field_prefix="nested")

        obj = SourceObj(nested=Nested(prop1=1234))

        test_writer(file, [obj])
    """
    columns = [column for column, _ in fields]
    field_mappers = [(column, _get_field_mapper(field)) for column, field in fields]
    prefix_mapper = attrgetter(field_prefix) if field_prefix is not None else None

    def _map_row(row):
        if prefix_mapper:
            row = prefix_mapper(row)
        return {column: field_mapper(row) for column, field_mapper in field_mappers}

    def _writer(file, rows):
        tsv_writer = csv.DictWriter(
            file,
            columns,
            dialect=PEARSON_CSV_DIALECT,
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


def _profile_country_to_alpha3(profile):
    """
    Returns the alpha3 code of a profile's country
    """
    # Pearson requires ISO-3166 alpha3 codes, but we store as alpha2
    try:
        country = pycountry.countries.get(alpha_2=profile.country)
    except KeyError as exc:
        raise InvalidProfileDataException() from exc
    return country.alpha_3


write_cdd_file = _tsv_writer([
    ('ClientCandidateId', 'student_id'),
    ('FirstName', 'romanized_first_name'),
    ('LastName', 'romanized_last_name'),
    ('Email', 'user.email'),
    ('Address1', 'address1'),
    ('Address2', 'address2'),
    ('Address3', 'address3'),
    ('City', 'city'),
    ('State', 'state_or_territory'),
    ('PostalCode', 'postal_code'),
    ('Country', _profile_country_to_alpha3),
    ('Phone', 'phone_number'),
    ('PhoneCountryCode', 'phone_country_code'),
    ('LastUpdate', lambda profile: _format_datetime(profile.updated_on)),
], field_prefix='profile')


ead_writer = writer([
    ('AuthorizationTransactionType', 'operation'),
    ('ClientAuthorizationID', lambda _: settings.EXAMS_AUTHORIZATION_ID),
    ('ClientCandidateId', 'user.profile.student_id'),
    ('ExamSeriesCode', 'course.program.exam_series_code'),
    ('Modules', 'course.'),
    ('EligibilityApptDateFirst', 'date_first_eligible'),
    ('EligibilityApptDateLast', 'date_last_eligible'),
    ('LastUpdate', 'updated_on'),
])


def upload_tsv(file_path):
    """
    Upload the given TSV files to the remote
    """
    for key in [
            "EXAMS_SFTP_HOST",
            "EXAMS_SFTP_PASSWORD",
            "EXAMS_SFTP_PORT",
            "EXAMS_SFTP_UPLOAD_DIR",
            "EXAMS_SFTP_USERNAME",
    ]:
        if getattr(settings, key) is None:
            raise ImproperlyConfigured(
                "The {} setting is required".format(key)
            )

    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None  # ignore knownhosts
    with pysftp.Connection(
        host=str(settings.EXAMS_SFTP_HOST),
        port=int(settings.EXAMS_SFTP_PORT),
        username=str(settings.EXAMS_SFTP_USERNAME),
        password=str(settings.EXAMS_SFTP_PASSWORD),
        cnopts=cnopts,
    ) as sftp:
        with sftp.cd(settings.EXAMS_SFTP_UPLOAD_DIR):
            sftp.put(file_path)
