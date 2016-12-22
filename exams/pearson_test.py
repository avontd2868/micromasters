"""
Tests for exams.pearson module
"""
from datetime import datetime
from unittest import mock
from unittest.mock import patch

import io

from django.core.exceptions import ImproperlyConfigured
from django.db.models.signals import post_save
from django.test import TestCase
from factory.django import mute_signals

from exams.exceptions import InvalidProfileDataException
from exams.factories import ExamProfileFactory
from exams.pearson import (
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

        content = file.getvalue()

        assert content == (
            "ClientCandidateId\tFirstName\tLastName\t"
            "Email\tAddress1\tAddress2\tAddress3\t"
            "City\tState\tPostalCode\tCountry\t"
            "Phone\tPhoneCountryCode\tLastUpdate\r\n"
        )

    def test_write_cdd_file(self):  # pylint: disable=no-self-use
        """
        Tests cdd_writer against a set of profiles
        """
        file = io.StringIO()

        kwargs = {
            'profile__id': 14879,
            'profile__romanized_first_name': 'Jane',
            'profile__romanized_last_name': 'Smith',
            'profile__user__email': 'jane@example.com',
            'profile__address1': '1 Main St',
            'profile__address2': 'Room B345',
            'profile__city': 'Boston',
            'profile__state_or_territory': 'Massachusetts',
            'profile__country': 'US',
            'profile__postal_code': '02115',
            'profile__phone_number': '999-999-9999',
            'profile__phone_country_code': '1',
        }

        with mute_signals(post_save):
            exam_profiles = [ExamProfileFactory.create(**kwargs)]

        exam_profiles[0].profile.updated_on = datetime(2016, 5, 15, 15, 2, 55)

        write_cdd_file(file, exam_profiles)

        lines = file.getvalue().splitlines()

        row = lines[1]

        assert row == (
            "14879\tJane\tSmith\tjane@example.com\t"
            "1 Main St\tRoom B345\t\t"  # double tab is for blank address3
            "Boston\tMassachusetts\t02115\tUSA\t"
            "999-999-9999\t1\t2016/05/15 15:02:55"
        )

    def test_write_cdd_file_skips_invalid_state(self):  # pylint: disable=no-self-use
        """
        Tests write_cdd_file against a profile with invalid state
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

    def test_upload_tsv_fails_if_sftp_host_not_set(self):  # pylint: disable=no-self-use
        """
        Tests that upload raises ImproperlyConfigured if settings.EXAMS_SFTP_HOST is not set
        """

        with self.settings(
            EXAMS_SFTP_HOST=None,
        ), patch('pysftp.Connection') as connection_mock:
            from exams.pearson import upload_tsv

            with self.assertRaises(ImproperlyConfigured):
                upload_tsv('file.tsv')
                connection_mock.assert_not_called()

    def test_upload_tsv_fails_if_sftp_port_not_set(self):  # pylint: disable=no-self-use
        """
        Tests that upload raises ImproperlyConfigured if settings.EXAMS_SFTP_PORT is not set
        """

        with self.settings(
            EXAMS_SFTP_PORT=None,
        ), patch('pysftp.Connection') as connection_mock:
            from exams.pearson import upload_tsv

            with self.assertRaises(ImproperlyConfigured):
                upload_tsv('file.tsv')
                connection_mock.assert_not_called()

    def test_upload_tsv_fails_if_sftp_username_not_set(self):  # pylint: disable=no-self-use
        """
        Tests that upload raises ImproperlyConfigured if settings.EXAMS_SFTP_USERNAME is not set
        """

        with self.settings(
            EXAMS_SFTP_USERNAME=None,
        ), patch('pysftp.Connection') as connection_mock:
            from exams.pearson import upload_tsv

            with self.assertRaises(ImproperlyConfigured):
                upload_tsv('file.tsv')
                connection_mock.assert_not_called()

    def test_upload_tsv_fails_if_sftp_password_not_set(self):  # pylint: disable=no-self-use
        """
        Tests that upload raises ImproperlyConfigured if settings.EXAMS_SFTP_PASSWORD is not set
        """

        with self.settings(
            EXAMS_SFTP_PASSWORD=None,
        ), patch('pysftp.Connection') as connection_mock:
            from exams.pearson import upload_tsv

            with self.assertRaises(ImproperlyConfigured):
                upload_tsv('file.tsv')
                connection_mock.assert_not_called()

    def test_upload_tsv_fails_if_sftp_upload_dir_not_set(self):  # pylint: disable=no-self-use
        """
        Tests that upload raises ImproperlyConfigured if settings.EXAMS_SFTP_UPLOAD_DIR is not set
        """

        with self.settings(
            EXAMS_SFTP_UPLOAD_DIR=None,
        ), patch('pysftp.Connection') as connection_mock:
            from exams.pearson import upload_tsv

            with self.assertRaises(ImproperlyConfigured):
                upload_tsv('file.tsv')
                connection_mock.assert_not_called()
