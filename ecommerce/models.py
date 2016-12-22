"""
Models for storing ecommerce data
"""
from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import (
    Model,
    SET_NULL,
)
from django.db.models.fields import (
    BooleanField,
    CharField,
    DateTimeField,
    DecimalField,
    TextField,
)
from django.db.models.fields.related import (
    ForeignKey,
)

from courses.models import CourseRun
from ecommerce.exceptions import EcommerceModelException
from micromasters.models import (
    AuditableModel,
    AuditModel,
)
from micromasters.utils import serialize_model_object


class Order(AuditableModel):
    """
    An order for financial aid programs
    """
    FULFILLED = 'fulfilled'
    FAILED = 'failed'
    CREATED = 'created'
    REFUNDED = 'refunded'

    STATUSES = [CREATED, FULFILLED, FAILED, REFUNDED]

    user = ForeignKey(User)
    status = CharField(
        choices=[(status, status) for status in STATUSES],
        default=CREATED,
        max_length=30,
        db_index=True,
    )

    created_at = DateTimeField(auto_now_add=True)
    modified_at = DateTimeField(auto_now=True)
    total_price_paid = DecimalField(decimal_places=2, max_digits=20)

    def __str__(self):
        """Description for Order"""
        return "Order {}, status={} for user={}".format(self.id, self.status, self.user)

    @classmethod
    def get_audit_class(cls):
        return OrderAudit

    def to_dict(self):
        """
        Get a serialized representation of the Order and any attached Lines
        """
        data = serialize_model_object(self)
        data['lines'] = [serialize_model_object(line) for line in self.line_set.all()]
        return data


class OrderAudit(AuditModel):
    """
    Audit model for Order
    """
    order = ForeignKey(Order, null=True, on_delete=SET_NULL)

    @classmethod
    def get_related_field_name(cls):
        return 'order'


class Line(Model):
    """
    A line in an order. This contains information about a specific item to be purchased.
    """
    course_key = TextField(db_index=True)
    order = ForeignKey(Order)
    price = DecimalField(decimal_places=2, max_digits=20)
    description = TextField(blank=True, null=True)

    created_at = DateTimeField(auto_now_add=True)
    modified_at = DateTimeField(auto_now=True)

    def __str__(self):
        """Description for Line"""
        return "Line for order {}, course_key={}, price={}".format(self.order.id, self.course_key, self.price)


class Receipt(Model):
    """
    The contents of the message from CyberSource about an Order fulfillment or cancellation
    """
    order = ForeignKey(Order, null=True)
    data = JSONField()

    created_at = DateTimeField(auto_now_add=True)
    modified_at = DateTimeField(auto_now=True)

    def __str__(self):
        """Description of Receipt"""
        if self.order:
            return "Receipt for order {}".format(self.order.id)
        else:
            return "Receipt with no attached order"


class CoursePrice(Model):
    """
    Information about a course run's price and other ecommerce info
    """
    course_run = ForeignKey(CourseRun)
    price = DecimalField(decimal_places=2, max_digits=20)
    is_valid = BooleanField(default=False)

    created_at = DateTimeField(auto_now_add=True)
    modified_at = DateTimeField(auto_now=True)

    def clean(self):
        """
        Override clean to provide user-friendly validation around CoursePrice.is_valid
        """
        if self.is_valid and CoursePrice.objects.filter(
                course_run=self.course_run,
                is_valid=True
        ).exclude(id=self.id).exists():
            raise ValidationError({
                'is_valid': 'Cannot have two CoursePrice objects for same CourseRun marked is_valid',
            })

    @transaction.atomic
    def save(self, *args, **kwargs):
        """
        Override save to make sure is_valid is only set per one CourseRun
        """
        if self.is_valid and CoursePrice.objects.filter(
                course_run=self.course_run,
                is_valid=True
        ).exclude(id=self.id).exists():
            raise EcommerceModelException("Cannot have two CoursePrice objects for same CourseRun marked is_valid")

        super(CoursePrice, self).save(*args, **kwargs)

    def __str__(self):
        """Description for CoursePrice"""
        return "CoursePrice for {}, price={}, is_valid={}".format(self.course_run, self.price, self.is_valid)


class Coupon(Model):
    """
    Model for coupons representing discounts on purchases
    """
    CREATED = 'created'
    USED = 'used'
    DELETED = 'deleted'
    STATUSES = [CREATED, USED, DELETED]

    PERCENT_DISCOUNT = 'percent-discount'
    FIXED_DISCOUNT = 'fixed-discount'

    AMOUNT_TYPES = [PERCENT_DISCOUNT, FIXED_DISCOUNT]

    COURSE_RUN = 'course-run'
    COURSE = 'course'
    PROGRAM = 'program'
    PRODUCT_TYPES = [PROGRAM, COURSE, COURSE_RUN]

    order = ForeignKey(Order, null=True)
    status = CharField(
        choices=[(status, status) for status in STATUSES],
        max_length=30,
    )
    amount_type = CharField(
        choices=[(_type, _type) for _type in AMOUNT_TYPES],
        max_length=30,
    )
    product_type = CharField(
        choices=[(_type, _type) for _type in PRODUCT_TYPES],
        max_length=30,
    )
    # Either a number from 0 to 1 representing a percent, or a fixed value for discount
    amount = DecimalField(decimal_places=2, max_digits=20)
    expiration_date = DateTimeField(null=True)

    def __str__(self):
        """Description for Coupon"""
        return (
            "Coupon with product_type={product_type}, product_id={product_id},"
            " amount_type={amount_type}, amount={amount}, order={order}".format(
                product_type=self.product_type,
                product_id=self.product_id,
                amount_type=self.amount_type,
                amount=self.amount,
                order=self.order,
            )
        )
