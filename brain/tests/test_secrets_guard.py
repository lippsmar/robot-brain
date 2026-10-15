"""Tests for the secret detection used by the event log and the memory."""

import pytest

from brain.secrets_guard import find_secret


@pytest.mark.parametrize(
    "data",
    [
        {"api_key": "x"},
        {"apiKey": "x"},
        {"APIKey": "x"},
        {"accessToken": "x"},
        {"clientSecret": "x"},
        {"dbPassword": "x"},
        {"sim_pin": "1234"},
        {"Passwort": "geheim"},
        {"headers": {"Authorization": "irgendwas"}},
        {"credentials": {"user": "a"}},
        {"note": "Authorization: Bearer abcdefghijklmnopqrstuvwxyz123456"},
        {"note": "sk-ant-api03-abcdefghijklmnop"},
        {"note": "sk-proj-abcdefghijklmnopqrstuvwxyz"},
        {"note": "ghp_abcdefghijklmnopqrstuvwxyz0123456789"},
        {"note": "AKIAABCDEFGHIJKLMNOP"},
        {"note": "123456789:ABCdefGHIjklMNOpqrSTUvwxYZ0123456789"},
        {"items": ["-----BEGIN OPENSSH PRIVATE KEY-----"]},
    ],
)
def test_secrets_are_found(data):
    assert find_secret(data) is not None


@pytest.mark.parametrize(
    "data",
    [
        {"pin": 16, "action": "beep"},  # GPIO pin of the buzzer
        {"gpio_pin": 4},
        {"input_tokens": 10, "max_tokens": 100, "output_tokens": 5},
        {"token_count": 12},
        {"spinner": "an"},
        {"note": "Das Passwort liegt im Secret-Store, Referenz secret://mail"},
        {"note": "Key-Länge 32 Zeichen"},
    ],
)
def test_harmless_data_passes(data):
    assert find_secret(data) is None
