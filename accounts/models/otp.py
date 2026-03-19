from datetime import timedelta
from django.db import models
from django.utils import timezone
from django.conf import settings
import random
import string

OTP_EXPIRATION_TIME = settings.OTP_EXPIRATION_TIME


class OTPTypeChoices(models.TextChoices):
    RESET_PASSWORD = "RESET_PASSWORD", "Reset Password"


def generate_otp():
    return "".join(random.choices(string.digits, k=6))


class OTP(models.Model):
    email = models.CharField(max_length=255)
    code = models.CharField(max_length=6, default=generate_otp)
    type = models.CharField(max_length=255, choices=OTPTypeChoices.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        return self.created_at >= timezone.now() - timedelta(
            minutes=OTP_EXPIRATION_TIME
        )

    @classmethod
    def verify_otp(cls, email, otp, otp_type):
        if not settings.EMAIL_SERVICE_ACTIVE:
            return True
        otp_obj = cls.objects.filter(email=email, code=otp, type=otp_type).first()
        if not otp_obj:
            return False
        elif not otp_obj.is_valid():
            otp_obj.delete()
            return False
        # Delete OTP after successful verification to prevent reuse
        otp_obj.delete()
        return True

    class Meta:
        ordering = ("-created_at",)
