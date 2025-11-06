import re
import requests
from django.core.exceptions import ValidationError


def validate_image_url(url):
    valid_image_extensions = re.compile(r'\.(jpg|jpeg|png|gif|bmp|webp|tiff)$', re.IGNORECASE)
    if not valid_image_extensions.search(url):
        raise ValidationError("URL does not point to a valid image file extension.")
    
    try:
        response = requests.head(url, allow_redirects=True)
        content_type = response.headers.get('Content-Type', '').lower()
        if not content_type.startswith('image/'):
            raise ValidationError("URL does not point to a valid image.")
    except requests.RequestException:
        raise ValidationError("URL could not be reached.")
