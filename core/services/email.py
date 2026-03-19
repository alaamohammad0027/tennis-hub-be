from django.conf import settings
from django.db import transaction
from typing import Tuple, Union, List
from django.template.loader import render_to_string
import base64
import resend


class EmailProvider:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            resend.api_key = settings.RESEND_API_KEY
            self.from_email = settings.DEFAULT_FROM_EMAIL
            self._initialized = True

    def send_email_msg(
        self,
        to_emails: Union[str, List[str]],
        msg: str,
        subject: str = "Notification",
        html_message: str = None,
    ) -> Tuple[bool, str]:
        """
        Send email message.

        Args:
            to_emails: Single email or list of emails
            msg: Plain text message
            subject: Email subject
            html_message: Optional HTML version of message

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            to_emails = [to_emails] if isinstance(to_emails, str) else to_emails

            # Prepare HTML content
            if html_message:
                email_html = html_message
            else:
                # Convert plain text to basic HTML
                email_html = f"""
                <div style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    {msg.replace('\n', '<br>')}
                </div>
                """

            successful_sends = 0
            failed_sends = []

            # Send to each recipient
            for email in to_emails:
                try:
                    result = resend.Emails.send(
                        {
                            "from": self.from_email,
                            "to": email,
                            "subject": subject,
                            "html": email_html,
                            "text": msg,
                        }
                    )

                    print(f"✅ Email sent to {email}. ID: {result.get('id', 'N/A')}")
                    successful_sends += 1

                except Exception as e:
                    print(f"❌ Failed to send email to {email}: {str(e)}")
                    failed_sends.append(email)

            if successful_sends == len(to_emails):
                return True, f"Sent to {successful_sends} recipient(s)"
            elif successful_sends > 0:
                return (
                    True,
                    f"Sent to {successful_sends}/{len(to_emails)} recipients. Failed: {', '.join(failed_sends)}",
                )
            else:
                return (
                    False,
                    f"Failed to send to all recipients: {', '.join(failed_sends)}",
                )

        except Exception as e:
            return False, f"Error: {str(e)}"

    def send_email_with_attachment(
        self,
        to_email: str,
        subject: str,
        html_message: str,
        msg: str,
        attachment_bytes: bytes,
        attachment_filename: str,
    ) -> Tuple[bool, str]:
        """Send a single email with one binary attachment.

        Args:
            to_email: Recipient address
            subject: Email subject
            html_message: HTML body
            msg: Plain-text body
            attachment_bytes: Raw bytes of the attachment
            attachment_filename: Filename shown to the recipient (e.g. "badge.png")

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            encoded = base64.b64encode(attachment_bytes).decode("utf-8")
            result = resend.Emails.send(
                {
                    "from": self.from_email,
                    "to": to_email,
                    "subject": subject,
                    "html": html_message,
                    "text": msg,
                    "attachments": [
                        {
                            "filename": attachment_filename,
                            "content": encoded,
                        }
                    ],
                }
            )
            print(f"✅ Badge email sent to {to_email}. ID: {result.get('id', 'N/A')}")
            return True, f"Sent to {to_email}"
        except Exception as e:
            print(f"❌ Failed to send badge email to {to_email}: {str(e)}")
            return False, f"Error: {str(e)}"


class OTPService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.email_provider = EmailProvider()
        return cls._instance

    @staticmethod
    def generate_otp(email: str, otp_type: str) -> Tuple[bool, str]:
        """Generate and send OTP via email."""
        from accounts.models import OTP

        if not settings.EMAIL_SERVICE_ACTIVE:
            return True, "OTP sent (service disabled)"

        try:
            with transaction.atomic():
                otp_obj = OTP.objects.create(email=email, type=otp_type)

                # Render HTML template
                html_message = render_to_string(
                    "emails/otp_email.html",
                    {
                        "otp_code": otp_obj.code,
                        "expiration_minutes": settings.OTP_EXPIRATION_TIME,
                    },
                )

                message = f"{otp_obj.code} is your OTP. Valid for {settings.OTP_EXPIRATION_TIME} minutes"

                return EmailProvider().send_email_msg(
                    to_emails=email,
                    msg=message,
                    subject="Your Verification Code",
                    html_message=html_message,
                )

        except Exception as e:
            return False, f"Error generating OTP: {str(e)}"
