"""Unit tests for the Emailer / SMTPConfigError."""
from __future__ import annotations

import smtplib
from unittest.mock import MagicMock, patch

import pytest

from tools.emailer import Emailer, SMTPConfigError

REQUIRED = {
    "SMTP_HOST": "smtp.example.com",
    "SMTP_PORT": "587",
    "SMTP_USER": "user",
    "SMTP_PASSWORD": "pass",
    "SENDER_EMAIL": "me@example.com",
    "RECIPIENT_EMAIL": "you@example.com",
}


def _set_env(monkeypatch):
    for k, v in REQUIRED.items():
        monkeypatch.setenv(k, v)


def test_init_defaults_port_when_unset(monkeypatch):
    _set_env(monkeypatch)
    monkeypatch.delenv("SMTP_PORT", raising=False)
    e = Emailer()
    assert e.smtp_port == 587


def test_init_lists_missing_vars(monkeypatch):
    _set_env(monkeypatch)
    monkeypatch.delenv("SMTP_USER", raising=False)
    monkeypatch.delenv("SENDER_EMAIL", raising=False)
    with pytest.raises(SMTPConfigError) as exc:
        Emailer()
    assert set(exc.value.missing) == {"SMTP_USER", "SENDER_EMAIL"}


def test_init_bad_port(monkeypatch):
    _set_env(monkeypatch)
    monkeypatch.setenv("SMTP_PORT", "not-a-port")
    with pytest.raises(SMTPConfigError) as exc:
        Emailer()
    assert exc.value.missing == ["SMTP_PORT"]


def test_send_email_success(monkeypatch):
    _set_env(monkeypatch)
    fake_server = MagicMock(spec=smtplib.SMTP)
    with patch("tools.emailer.smtplib.SMTP", return_value=fake_server):
        result = Emailer().send_email("subj", "body")
    assert result is True
    fake_server.starttls.assert_called_once()
    fake_server.login.assert_called_once()
    fake_server.sendmail.assert_called_once()
    fake_server.quit.assert_called_once()


def test_send_email_smtp_failure(monkeypatch):
    _set_env(monkeypatch)
    fake_server = MagicMock(spec=smtplib.SMTP)
    fake_server.login.side_effect = smtplib.SMTPAuthenticationError(535, b"no")
    with patch("tools.emailer.smtplib.SMTP", return_value=fake_server):
        result = Emailer().send_email("subj", "body")
    assert result is False
    fake_server.quit.assert_called_once()
