"""
util functions for profiles
"""
from datetime import datetime
from io import BytesIO
from os import path

from PIL import Image
import pytz

# This is the Django ImageField max path size
IMAGE_PATH_MAX_LENGTH = 100

# Max dimension of either height or width for a small image
IMAGE_SMALL_MAX_DIMENSION = 64


def split_name(name):
    """
    Split a name into two names. If there is only one name, the last name will be
    empty. If there are more than two, the extra names will be appended to the last
    name.

    Args:
        name (str): A name to split into first name, last name
    Returns:
        tuple: (first, last)
    """
    if name is None:
        return "", ""
    names = name.split(maxsplit=1)
    if len(names) == 0:
        return "", ""
    else:
        return names[0], " ".join(names[1:])


def _generate_upload_to_uri(suffix=""):
    """
    Returns a function to specify the upload directory and filename, via upload_to on an ImageField

    Args:
        suffix (str):
            A suffix for the filename
    Returns:
        function:
            A function to use with upload_to to specify an upload directory and filename
    """

    def _upload_to(_, filename):
        """Function passed to upload_to on an ImageField"""
        name, ext = path.splitext(filename)
        timestamp = datetime.now(pytz.utc).replace(microsecond=0)
        path_format = "profile/{name}-{timestamp}{suffix}{ext}"

        path_without_name = path_format.format(
            timestamp=timestamp.strftime("%Y-%m-%dT%H%M%S-%z"),
            suffix=suffix,
            ext=ext,
            name='',
        )
        if len(path_without_name) >= IMAGE_PATH_MAX_LENGTH:
            raise Exception("path is longer than max length even without name: {}".format(path_without_name))

        max_name_length = IMAGE_PATH_MAX_LENGTH - len(path_without_name)
        full_path = path_format.format(
            name=name[:max_name_length],
            timestamp=timestamp.strftime("%Y-%m-%dT%H%M%S-%z"),
            suffix=suffix,
            ext=ext,
        )

        return full_path
    return _upload_to


# These two functions are referenced in migrations so be careful refactoring
def profile_image_upload_uri(instance, filename):
    """
    upload_to handler for Profile.image
    """
    return _generate_upload_to_uri()(instance, filename)


def profile_image_upload_uri_small(instance, filename):
    """
    upload_to handler for Profile.image_small
    """
    return _generate_upload_to_uri("_small")(instance, filename)


def make_small_dimensions(width, height):
    """
    Resize dimensions so max dimension is IMAGE_SMALL_MAX_DIMENSION. If dimensions are too small no resizing is done
    Args:
        width (int): The width
        height (int): The height
    Returns:
        tuple of (small_width, small_height): A resized set of dimensions, as integers
    """
    max_width_height = max(width, height)
    if max_width_height < IMAGE_SMALL_MAX_DIMENSION:
        return width, height
    ratio = max_width_height / IMAGE_SMALL_MAX_DIMENSION

    return int(width / ratio), int(height / ratio)


def make_thumbnail(full_size_image):
    """
    Make a thumbnail of the image

    Args:
        full_size_image (file):
            A file-like object containing an image. This file will seek back to the beginning after being read.
    Returns:
        BytesIO:
            A jpeg image which is a thumbnail of full_size_image
    """
    in_memory_image = full_size_image
    pil_image = Image.open(in_memory_image)
    pil_image.thumbnail(make_small_dimensions(pil_image.width, pil_image.height), Image.ANTIALIAS)
    image_small_buffer = BytesIO()
    pil_image.save(image_small_buffer, "JPEG", quality=90)
    image_small_buffer.seek(0)
    in_memory_image.seek(0)
    return image_small_buffer
