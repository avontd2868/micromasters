"""
APIs for extending the python social auth pipeline
"""
import logging
from urllib.parse import urljoin

from profiles.models import Profile

log = logging.getLogger(__name__)


def update_profile_from_edx(backend, user, response, is_new, *args, **kwargs):   # pylint: disable=unused-argument
    """
    Gets profile information from EDX and saves them in the user profile

    Args:
        backend (social.backends.oauth.BaseOAuth2): the python social auth backend
        user (User): user object
        response (dict): dictionary of the user information coming
            from previous functions in the pipeline
        is_new (bool): whether the authenticated user created a new local instance

    Returns:
        None
    """

    # this function is completely skipped if the backend is not edx or
    # the user has not created now
    if backend.name != 'edxorg' or not is_new:
        return

    access_token = response.get('access_token')
    if not access_token:
        # this should never happen for the edx oauth provider, but just in case...
        log.error('Missing access token for the user %s', user.username)
        return

    try:
        user_profile = Profile.objects.get(user=user)
    except Profile.DoesNotExist:
        # this should never happen, since the profile is created with a signal
        # right after the user is created
        log.error('No profile found for the user %s', user.username)
        return

    user_profile_edx = backend.get_json(
        urljoin(backend.EDXORG_BASE_URL, '/api/user/v1/accounts/{0}'.format(user.username)),
        headers={
            "Authorization": "Bearer {}".format(access_token),
        }
    )

    user_profile.account_privacy = user_profile_edx.get('account_privacy')
    user_profile.name = user_profile_edx.get('name')
    user_profile.bio = user_profile_edx.get('bio')
    user_profile.country = user_profile_edx.get('country')
    user_profile.has_profile_image = user_profile_edx.get(
        'profile_image', {}).get('has_image')
    user_profile.profile_url_full = user_profile_edx.get(
        'profile_image', {}).get('image_url_full')
    user_profile.profile_url_large = user_profile_edx.get(
        'profile_image', {}).get('image_url_large')
    user_profile.profile_url_medium = user_profile_edx.get(
        'profile_image', {}).get('image_url_medium')
    user_profile.profile_url_small = user_profile_edx.get(
        'profile_image', {}).get('image_url_small')
    user_profile.requires_parental_consent = user_profile_edx.get('requires_parental_consent')
    user_profile.year_of_birth = user_profile_edx.get('year_of_birth')
    user_profile.level_of_education = user_profile_edx.get('level_of_education')
    user_profile.goals = user_profile_edx.get('goals')
    user_profile.language_proficiencies = user_profile_edx.get('language_proficiencies')
    user_profile.gender = user_profile_edx.get('gender')
    user_profile.mailing_address = user_profile_edx.get('mailing_address')

    user_profile.save()

    log.debug(
        'Profile for user "%s" updated with values from EDX %s',
        user.username,
        user_profile_edx
    )