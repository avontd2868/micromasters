"""
Tests for exams.pearson module
"""
from unittest.mock import patch

import datetime
import io

from django.db.models.signals import post_save
from django.test import TestCase
from factory.django import mute_signals

import pycountry
import pytz

from exams.exceptions import InvalidProfileDataException
from exams.pearson import (
    CCD_FIELD_NAMES,
    LAST_UPDATE_FORMAT,
    write_profiles_ccd,
    profile_to_ccd_row,
)
from profiles.factories import ProfileFactory


class PearsonTest(TestCase):
    """
    Tests for Pearson code
    """

    def test_profile_to_ccd_row(self):  # pylint: disable=no-self-use
        """
        Test that profile_to_ccd_row returns a dict row
        """
        with mute_signals(post_save):
            profile = ProfileFactory.create()
        profile.updated_on = datetime.datetime(2014, 12, 17, 15, 45, 0, tzinfo=pytz.utc)

        row = profile_to_ccd_row(profile)
        country = pycountry.countries.get(alpha_2=profile.country)

        assert isinstance(row, dict)
        assert row['ClientCandidateId'] == profile.student_id
        assert row['FirstName'] == profile.romanized_first_name
        assert row['LastName'] == profile.romanized_last_name
        assert row['Email'] == profile.user.email
        assert row['Address1'] == profile.address1
        assert row['Address2'] == profile.address2
        assert row['City'] == profile.city
        assert row['State'] == profile.state_or_territory
        assert row['PostalCode'] == profile.postal_code
        assert row['Country'] == country.alpha_3
        assert row['Phone'] == profile.phone_number
        assert row['PhoneCountryCode'] == profile.phone_country_code
        assert row['LastUpdate'] == '2014-12-17 15:45:00'

        assert 'Address3' not in row

    def test_profile_to_ccd_row_invalid_country(self):  # pylint: disable=no-self-use
        """
        A profile with an invalid country code should raise an InvalidProfileDataException
        """
        with mute_signals(post_save):
            profile = ProfileFactory.create()
        profile.country = 'XXXX'
        with self.assertRaises(InvalidProfileDataException):
            profile_to_ccd_row(profile)

    def test_write_profiles_ccd_no_profiles(self):  # pylint: disable=no-self-use
        """
        Tests write_profiles_ccd against an empty set of profiles
        """
        file = io.StringIO()

        write_profiles_ccd([], file)

        lines = file.getvalue().splitlines()

        assert lines == [
            '\t'.join(CCD_FIELD_NAMES),
        ]

    def test_write_profiles_ccd(self):  # pylint: disable=no-self-use
        """
        Tests write_profiles_ccd against a set of profiles
        """
        file = io.StringIO()

        profiles = []
        with mute_signals(post_save):
            profiles.extend(ProfileFactory.create_batch(5))
            profiles.extend(ProfileFactory.create_batch(5, address3='Room B345'))
            profiles.extend(ProfileFactory.create_batch(5, address2=None))

        write_profiles_ccd(profiles, file)

        lines = file.getvalue().splitlines()

        header, rows = lines[0], lines[1:]

        assert header == '\t'.join(CCD_FIELD_NAMES)

        for idx, profile in enumerate(profiles):
            row = rows[idx]
            country = pycountry.countries.get(alpha_2=profile.country)
            assert row == ('\t'.join(map(str, [
                profile.student_id,
                profile.romanized_first_name,
                profile.romanized_last_name,
                profile.user.email,
                profile.address1,
                profile.address2 or '',
                profile.address3 or '',
                profile.city,
                profile.state_or_territory,
                profile.postal_code,
                country.alpha_3,
                profile.phone_number,
                profile.phone_country_code,
                profile.updated_on.strftime(LAST_UPDATE_FORMAT),
            ])))

            for cell in row.split('\t'):
                assert cell != 'None'

    def test_write_profiles_ccd_skips_invalid_state(self):  # pylint: disable=no-self-use
        """
        Tests write_profiles_ccd against a profiel with invalid state
        """
        file = io.StringIO()

        with mute_signals(post_save):
            profiles = [ProfileFactory.create(country='00')]

        write_profiles_ccd(profiles, file)

        lines = file.getvalue().splitlines()

        _, rows = lines[0], lines[1:]

        assert len(rows) == 0

    def test_upload_tsv(self):  # pylint: disable=no-self-use
        """
        Tests that upload uses the correct settings values
        """
        EXAMS_SFTP_HOST = 'l0calh0st',
        EXAMS_SFTP_USERNAME = 'username',
        EXAMS_SFTP_PASSWORD = 'password'
        EXAMS_SFTP_PUT_DIR = '/tmp'
        FILENAME = 'FILENAME'

        with self.settings(
            EXAMS_SFTP_HOST=EXAMS_SFTP_HOST,
            EXAMS_SFTP_USERNAME=EXAMS_SFTP_USERNAME,
            EXAMS_SFTP_PASSWORD=EXAMS_SFTP_PASSWORD,
            EXAMS_SFTP_PUT_DIR=EXAMS_SFTP_PUT_DIR
        ), patch('pysftp.Connection') as connection_mock:
            from exams.pearson import upload_tsv

            upload_tsv(FILENAME)
            connection_mock.assert_called_with(
                EXAMS_SFTP_HOST,
                EXAMS_SFTP_PORT,
                EXAMS_SFTP_USERNAME,
                EXAMS_SFTP_PASSWORD,
            )

            ftp_mock = connection_mock.return_value.__enter__.return_value
            ftp_mock.cd.assert_called_with(EXAMS_SFTP_PUT_DIR)
            ftp_mock.put.assert_called_with(FILENAME)
