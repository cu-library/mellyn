"""
This module defines signal triggered callbacks for this application.

https://docs.djangoproject.com/en/3.0/topics/signals/
"""

from django.conf import settings
from django.core.mail import send_mail

from .models import LicenseCode


def warn_low_number_unassigned_licensecodes(sender, **kwargs):  # pylint: disable=unused-argument
    """
    Send an email if the number of unassigned license codes for a resource
    falls below that recource's low codes threshold, if the number of codes
    remaning is divisible by 10.
    """

    if 'instance' not in kwargs:
        return
    resource = kwargs['instance'].resource
    if resource.low_codes_email == '':
        return
    num_rem = LicenseCode.objects.filter(resource=resource, signature__isnull=True).count()
    if num_rem > resource.low_codes_threshold:
        return
    if (num_rem % 10) != 0:
        return

    send_mail(
        f'Sign - Warning: {num_rem} unassigned license codes for {resource.name}',
        f'{resource.name} has {num_rem} unassigned License Codes left! It might be time to add more.',
        settings.DEFAULT_FROM_EMAIL,
        [resource.low_codes_email],
        fail_silently=False
    )
