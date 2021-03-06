"""
Functions for ecommerce
"""
from base64 import b64encode
from datetime import datetime
import hashlib
import hmac
import logging
from urllib.parse import quote_plus
import uuid

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from django.http.response import Http404
from django.shortcuts import get_object_or_404
from edx_api.client import EdxApi
import pytz
from rest_framework.exceptions import ValidationError

from backends.edxorg import EdxOrgOAuth2
from courses.models import CourseRun
from dashboard.api_edx_cache import CachedEdxDataApi
from dashboard.models import ProgramEnrollment
from ecommerce.exceptions import (
    EcommerceEdxApiException,
    EcommerceException,
    ParseException,
)
from ecommerce.models import (
    Line,
    Order,
)
from financialaid.api import get_formatted_course_price
from financialaid.models import (
    FinancialAid,
    FinancialAidStatus,
)
from profiles.api import get_social_username


ISO_8601_FORMAT = '%Y-%m-%dT%H:%M:%SZ'
log = logging.getLogger(__name__)
_REFERENCE_NUMBER_PREFIX = 'MM-'


def get_purchasable_course_run(course_key, user):
    """
    Gets a course run, or raises Http404 if not purchasable. To be purchasable a course run
    must not already be purchased, must be part of a live program, must be part of a program
    with financial aid enabled, with a financial aid object, and must have a valid price.

    Args:
        course_key (str):
            An edX course key
        user (User):
            The purchaser of the course run
    Returns:
        CourseRun: A course run
    """
    # Make sure it's connected to a live program, it has a valid price, and the user is enrolled in the program already
    try:
        course_run = get_object_or_404(
            CourseRun,
            edx_course_key=course_key,
            course__program__live=True,
            course__program__financial_aid_availability=True,
            courseprice__is_valid=True,
        )
    except Http404:
        log.warning("Course run %s is not purchasable", course_key)
        raise

    if not FinancialAid.objects.filter(
            tier_program__current=True,
            tier_program__program__course__courserun=course_run,
            user=user,
            status__in=FinancialAidStatus.TERMINAL_STATUSES,
    ).exists():
        log.warning("Course run %s has no attached financial aid for user %s", course_key, get_social_username(user))
        raise ValidationError(
            "Course run {} does not have a current attached financial aid application".format(course_key)
        )

    # Make sure it's not already purchased
    if Line.objects.filter(
            order__status=Order.FULFILLED,
            order__user=user,
            course_key=course_run.edx_course_key,
    ).exists():
        log.warning("Course run %s is already purchased by user %s", course_key, user)
        raise ValidationError("Course run {} is already purchased".format(course_key))

    return course_run


@transaction.atomic
def create_unfulfilled_order(course_id, user):
    """
    Create a new Order which is not fulfilled for a purchasable course run. If course run is not purchasable,
    it raises an Http404

    Args:
        course_id (str):
            A course key
        user (User):
            The purchaser of the course run
    Returns:
        Order: A newly created Order for the CourseRun with the given course_id
    """
    course_run = get_purchasable_course_run(course_id, user)
    enrollment = get_object_or_404(ProgramEnrollment, program=course_run.course.program, user=user)
    price_dict = get_formatted_course_price(enrollment)
    price = price_dict['price']
    if price <= 0:
        log.error(
            "Price to be charged for course run %s for user %s is less than or equal to zero: %s",
            course_id,
            get_social_username(user),
            price,
        )
        raise ImproperlyConfigured("Price to be charged is less than or equal to zero")

    order = Order.objects.create(
        status=Order.CREATED,
        total_price_paid=price,
        user=user,
    )
    Line.objects.create(
        order=order,
        course_key=course_run.edx_course_key,
        description='Seat for {}'.format(course_run.title),
        price=price,
    )
    order.save_and_log(user)
    return order


def generate_cybersource_sa_signature(payload):
    """
    Generate an HMAC SHA256 signature for the CyberSource Secure Acceptance payload

    Args:
        payload (dict): The payload to be sent to CyberSource
    Returns:
        str: The signature
    """
    # This is documented in certain CyberSource sample applications:
    # http://apps.cybersource.com/library/documentation/dev_guides/Secure_Acceptance_SOP/html/wwhelp/wwhimpl/js/html/wwhelp.htm#href=creating_profile.05.6.html
    keys = payload['signed_field_names'].split(',')
    message = ','.join('{}={}'.format(key, payload[key]) for key in keys)

    digest = hmac.new(
        settings.CYBERSOURCE_SECURITY_KEY.encode('utf-8'),
        msg=message.encode('utf-8'),
        digestmod=hashlib.sha256,
    ).digest()

    return b64encode(digest).decode('utf-8')


def generate_cybersource_sa_payload(order, dashboard_url):
    """
    Generates a payload dict to send to CyberSource for Secure Acceptance

    Args:
        order (Order): An order
        dashboard_url: (str): The absolute url for the dashboard
    Returns:
        dict: the payload to send to CyberSource via Secure Acceptance
    """
    # http://apps.cybersource.com/library/documentation/dev_guides/Secure_Acceptance_WM/Secure_Acceptance_WM.pdf
    # Section: API Fields

    # Course key is used only to show the confirmation message to the user
    course_key = ""
    line = order.line_set.first()
    if line is not None:
        course_key = line.course_key
    course_run = CourseRun.objects.get(edx_course_key=course_key)

    # NOTE: be careful about max length here, many (all?) string fields have a max
    # length of 255. At the moment none of these fields should go over that, due to database
    # constraints or other reasons

    payload = {
        'access_key': settings.CYBERSOURCE_ACCESS_KEY,
        'amount': str(order.total_price_paid),
        'consumer_id': get_social_username(order.user),
        'currency': 'USD',
        'locale': 'en-us',
        'item_0_code': 'course',
        'item_0_name': '{}'.format(course_run.title),
        'item_0_quantity': 1,
        'item_0_sku': '{}'.format(course_key),
        'item_0_tax_amount': '0',
        'item_0_unit_price': str(order.total_price_paid),
        'line_item_count': 1,
        'override_custom_cancel_page': "{}?status=cancel&course_key={}".format(
            dashboard_url,
            quote_plus(course_key),
        ),
        'override_custom_receipt_page': "{}?status=receipt&course_key={}".format(
            dashboard_url,
            quote_plus(course_key),
        ),
        'reference_number': make_reference_id(order),
        'profile_id': settings.CYBERSOURCE_PROFILE_ID,
        'signed_date_time': datetime.now(tz=pytz.UTC).strftime(ISO_8601_FORMAT),
        'transaction_type': 'sale',
        'transaction_uuid': uuid.uuid4().hex,
        'unsigned_field_names': '',
        'merchant_defined_data1': 'course',
        'merchant_defined_data2': '{}'.format(course_run.title),
        'merchant_defined_data3': '{}'.format(course_key),
    }

    field_names = sorted(list(payload.keys()) + ['signed_field_names'])
    payload['signed_field_names'] = ','.join(field_names)
    payload['signature'] = generate_cybersource_sa_signature(payload)

    return payload


def make_reference_id(order):
    """
    Make a reference id

    Args:
        order (Order):
            An order
    Returns:
        str:
            A reference number for use with CyberSource to keep track of orders
    """
    return "{}{}-{}".format(_REFERENCE_NUMBER_PREFIX, settings.CYBERSOURCE_REFERENCE_PREFIX, order.id)


def get_new_order_by_reference_number(reference_number):
    """
    Parse a reference number received from CyberSource and lookup the corresponding Order. If the Order
    is already fulfilled an EcommerceException is raised.

    Args:
        reference_number (str):
            A string which contains the order id and the instance which generated it
    Returns:
        Order:
            An order
    """
    if not reference_number.startswith(_REFERENCE_NUMBER_PREFIX):
        raise ParseException("Reference number must start with {}".format(_REFERENCE_NUMBER_PREFIX))
    reference_number = reference_number[len(_REFERENCE_NUMBER_PREFIX):]

    try:
        order_id_pos = reference_number.rindex('-')
    except ValueError:
        raise ParseException("Unable to find order number in reference number")

    try:
        order_id = int(reference_number[order_id_pos + 1:])
    except ValueError:
        raise ParseException("Unable to parse order number")

    prefix = reference_number[:order_id_pos]
    if prefix != settings.CYBERSOURCE_REFERENCE_PREFIX:
        log.error("CyberSource prefix doesn't match: %s != %s", prefix, settings.CYBERSOURCE_REFERENCE_PREFIX)
        raise ParseException("CyberSource prefix doesn't match")

    try:
        return Order.objects.get(id=order_id, status=Order.CREATED)
    except Order.DoesNotExist:
        raise EcommerceException("Order {} is expected to have status 'created'".format(order_id))


def enroll_user_on_success(order):
    """
    Enroll user after they made a successful purchase.

    Args:
        order (Order): An order to be fulfilled

    Returns:
         None
    """
    user_social = order.user.social_auth.get(provider=EdxOrgOAuth2.name)
    enrollments_client = EdxApi(user_social.extra_data, settings.EDXORG_BASE_URL).enrollments

    exceptions = []
    enrollments = []
    for line in order.line_set.all():
        course_key = line.course_key
        try:
            enrollments.append(enrollments_client.create_audit_student_enrollment(course_key))
        except Exception as ex:  # pylint: disable=broad-except
            log.exception(
                "Error creating audit enrollment for course key %s for user %s",
                course_key,
                get_social_username(order.user),
            )
            exceptions.append(ex)

    for enrollment in enrollments:
        CachedEdxDataApi.update_cached_enrollment(
            order.user,
            enrollment,
            enrollment.course_id,
            index_user=True,
        )

    if exceptions:
        raise EcommerceEdxApiException(exceptions)
