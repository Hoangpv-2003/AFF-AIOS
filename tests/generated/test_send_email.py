# -*- coding: utf-8 -*-

from __future__ import annotations

import pytest

from app.skills.dynamic.send_email import send_email


def test_send_email():
    result = send_email()
    assert isinstance(result, dict)
    assert 'status' in result
    assert result['status'] == 'success'
