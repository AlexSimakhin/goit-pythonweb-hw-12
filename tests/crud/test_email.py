"""Unit tests for email sending utilities using SMTP mocking."""
from unittest.mock import patch
import smtplib
from app.utils.auth import send_verification_email


def test_send_verification_email_success():
    """send_verification_email returns True on successful SMTP send."""
    with patch("smtplib.SMTP") as mock_smtp:
        server_mock = mock_smtp.return_value.__enter__.return_value
        server_mock.starttls.return_value = None
        server_mock.sendmail.return_value = {}
        result = send_verification_email("valid@example.com", 1)
        assert result is True


def test_send_verification_email_invalid_email():
    """send_verification_email returns False for invalid email input."""
    result = send_verification_email("invalid-email", 1)
    assert result is False


def test_send_verification_email_smtp_error():
    """send_verification_email returns False when SMTP raises an exception."""
    with patch("smtplib.SMTP", side_effect=smtplib.SMTPException("smtp error")):
        result = send_verification_email("valid@example.com", 1)
        assert result is False
