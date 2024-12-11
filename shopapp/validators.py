# In your Django app, create a file e.g., validators.py

from django.core.exceptions import ValidationError

def validate_phone_number(value):
    if not value.isdigit() or len(value) != 10:
        raise ValidationError('Phone number must be exactly 10 digits.')
