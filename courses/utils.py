"""
Utility functions for the courses app
"""
import re
from opaque_keys.edx.keys import CourseKey
from opaque_keys import InvalidKeyError

NUMBER_SEASON_MAP = {
    1: 'Spring',
    2: 'Summer',
    3: 'Fall'
}


def parse_edx_key(edx_course_key):
    """
    Args:
        edx_course_key (str): An edX course key (CourseRun.edx_course_key)

    Returns:
        The 'run' portion of a parsed CourseKey (opaque_keys.edx.keys.CourseKey#run).
        eg: '1T2016'
    """
    try:
        course_key = CourseKey.from_string(edx_course_key)
    except InvalidKeyError:
        return None
    return course_key.run if course_key else None


def get_year_season_from_edx_key(parsed_course_key):
    """
    Verifies that a parsed course key matches our expected format and returns a year/season

    Args:
        parsed_course_key (str): A semester/year indicator from a course key (eg: '1T2016')

    Returns:
        tuple: (Year, Season number)
    """
    found = re.search('^[1-3]T[1|2][0-9]{3}$', parsed_course_key)
    if found:
        season_year_tuple = found.group().split('T')
        return int(season_year_tuple[1]), int(season_year_tuple[0])
    return None, None


def get_year_season_from_dates(course_run):
    """
    Args:
        course_run (CourseRun): A CourseRun object

    Returns:
        tuple: (Year, Season number)
    """
    if not course_run.start_date:
        return None, None
    start_month = course_run.start_date.month
    if 1 <= start_month <= 4:
        season_num = 1
    elif 5 <= start_month <= 8:
        season_num = 2
    else:
        season_num = 3
    return course_run.start_date.year, season_num


def get_year_season_from_course_run(course_run):
    """
    Args:
        course_run (CourseRun): A CourseRun object

    Returns:
        tuple: (Year, Season string)
    """
    parsed_course_key = parse_edx_key(course_run.edx_course_key)
    if parsed_course_key:
        season_year_tuple = get_year_season_from_edx_key(parsed_course_key)
    else:
        season_year_tuple = get_year_season_from_dates(course_run)
    return season_year_tuple[0], NUMBER_SEASON_MAP[season_year_tuple[1]]
