# -*- coding: utf-8 -*-

import pytest

import director.config


def test_dummy():
    assert 1 == 1
    with pytest.raises(AssertionError):
        raise AssertionError
