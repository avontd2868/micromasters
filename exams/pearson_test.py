"""
Tests for exams.pearson module
"""
import datetime
import io
import pycountry
import pytz

from django.db.models.signals import post_save
from django.test import TestCase
from factory.django import mute_signals

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
        assert row['FirstName'] == profile.first_name
        assert row['LastName'] == profile.last_name
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
        Tests write_profiles_ccd against an empty set of profiles
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
                profile.first_name,
                profile.last_name,
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
