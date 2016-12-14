"""
Tests for exams.pearson module
"""
from unittest import mock
from unittest.mock import patch

import io

from django.db.models.signals import post_save
from django.test import TestCase
from factory.django import mute_signals

import pycountry

from exams.exceptions import InvalidProfileDataException
from exams.factories import ExamProfileFactory
from exams.pearson import (
    PEARSON_DATETIME_FORMAT,
    write_cdd_file,
    _get_field_mapper,
    _profile_country_to_alpha3
)
from profiles.factories import ProfileFactory


class PearsonTest(TestCase):
    """
    Tests for Pearson code
    """

    def test_get_field_mapper(self):  # pylint: disable=no-self-use
        """
        Tests that _get_field_mapper handles input correctly
        """
        with mute_signals(post_save):
            profile = ProfileFactory.create()

        def get_addr1(profile):  # pylint: disable=missing-docstring
            return profile.address1

        assert _get_field_mapper('address1')(profile) == profile.address1

        addr1_field_mapper = _get_field_mapper(get_addr1)

        assert addr1_field_mapper == get_addr1
        assert addr1_field_mapper(profile) == profile.address1

        with self.assertRaises(TypeError):
            _get_field_mapper([])

    def test_profile_country_to_alpha3_invalid_country(self):  # pylint: disable=no-self-use
        """
        A profile with an invalid country code should raise an InvalidProfileDataException
        """
        with mute_signals(post_save):
            profile = ProfileFactory.create()
        profile.country = 'XXXX'
        with self.assertRaises(InvalidProfileDataException):
            _profile_country_to_alpha3(profile)

    def test_write_profiles_cdd_no_profiles(self):  # pylint: disable=no-self-use
        """
        Tests write_cdd_file against an empty set of profiles
        """
        file = io.StringIO()

        write_cdd_file(file, [])

        lines = file.getvalue().splitlines()
        header = lines[0].split('\t')

        assert len(lines) == 1
        assert header == [
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

    def test_write_cdd_file(self):  # pylint: disable=no-self-use
        """
        Tests ccd_writer against a set of profiles
        """
        file = io.StringIO()

        exam_profile_kwargs = [
            {},
            {'profile__address3': 'Room B345'},
            {'profile__address2': None}
        ]

        with mute_signals(post_save):
            exam_profiles = [ExamProfileFactory.create(**kwargs) for kwargs in exam_profile_kwargs]

        write_cdd_file(file, exam_profiles)

        lines = file.getvalue().splitlines()

        rows = lines[1:]

        for idx, exam_profile in enumerate(exam_profiles):
            profile = exam_profile.profile
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
                profile.updated_on.strftime(PEARSON_DATETIME_FORMAT),
            ])))

            for cell in row.split('\t'):
                assert cell != 'None'

    def test_write_cdd_file_skips_invalid_state(self):  # pylint: disable=no-self-use
        """
        Tests write_cdd_file against a profiel with invalid state
        """
        file = io.StringIO()

        with mute_signals(post_save):
            profiles = [ExamProfileFactory.create(profile=ProfileFactory.create(country='XXXX'))]

        write_cdd_file(file, profiles)

        lines = file.getvalue().splitlines()

        _, rows = lines[0], lines[1:]

        assert len(rows) == 0

    def test_upload_tsv(self):  # pylint: disable=no-self-use
        """
        Tests that upload uses the correct settings values
        """
        EXAMS_SFTP_HOST = 'l0calh0st'
        EXAMS_SFTP_PORT = '345'
        EXAMS_SFTP_USERNAME = 'username'
        EXAMS_SFTP_PASSWORD = 'password'
        EXAMS_SFTP_UPLOAD_DIR = 'tmp'
        FILENAME = 'FILENAME'

        with self.settings(
            EXAMS_SFTP_HOST=EXAMS_SFTP_HOST,
            EXAMS_SFTP_PORT=EXAMS_SFTP_PORT,
            EXAMS_SFTP_USERNAME=EXAMS_SFTP_USERNAME,
            EXAMS_SFTP_PASSWORD=EXAMS_SFTP_PASSWORD,
            EXAMS_SFTP_UPLOAD_DIR=EXAMS_SFTP_UPLOAD_DIR
        ), patch('pysftp.Connection') as connection_mock:
            from exams.pearson import upload_tsv

            upload_tsv(FILENAME)
            connection_mock.assert_called_once_with(
                host=EXAMS_SFTP_HOST,
                port=int(EXAMS_SFTP_PORT),
                username=EXAMS_SFTP_USERNAME,
                password=EXAMS_SFTP_PASSWORD,
                cnopts=mock.ANY,
            )

            ftp_mock = connection_mock.return_value.__enter__.return_value
            ftp_mock.cd.assert_called_once_with(EXAMS_SFTP_UPLOAD_DIR)
            ftp_mock.put.assert_called_once_with(FILENAME)
