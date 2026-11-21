"""Tests for the OIDC PKCE and authorization-callback validation helpers."""

from __future__ import annotations

import base64
import hashlib

import pytest
from fastapi import HTTPException

from app.api.auth import (
    generate_pkce_challenge,
    generate_pkce_pair,
    generate_pkce_verifier,
    parse_callback_params,
    validate_callback_params,
    verify_pkce,
)


class TestPkceGeneration:
    def test_verifier_length_and_alphabet(self):
        verifier = generate_pkce_verifier()
        assert 43 <= len(verifier) <= 128
        assert set(verifier) <= set(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"
        )

    def test_verifiers_are_unique(self):
        assert len({generate_pkce_verifier() for _ in range(50)}) == 50

    def test_challenge_is_s256_of_verifier(self):
        verifier = "test-verifier-abcdefghijklmnopqrstuvwxyz0123456789"
        expected = (
            base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("ascii")).digest())
            .decode("ascii")
            .rstrip("=")
        )
        assert generate_pkce_challenge(verifier) == expected

    def test_challenge_has_no_padding(self):
        assert "=" not in generate_pkce_challenge(generate_pkce_verifier())

    def test_pair_round_trips(self):
        pair = generate_pkce_pair()
        assert pair.method == "S256"
        assert verify_pkce(pair.verifier, pair.challenge)


class TestVerifyPkce:
    def test_rejects_wrong_verifier(self):
        pair = generate_pkce_pair()
        assert not verify_pkce(generate_pkce_verifier(), pair.challenge)

    def test_rejects_plain_method(self):
        pair = generate_pkce_pair()
        assert not verify_pkce(pair.verifier, pair.verifier, method="plain")

    def test_rejects_case_variant_of_method(self):
        pair = generate_pkce_pair()
        assert verify_pkce(pair.verifier, pair.challenge, method="s256")
        assert not verify_pkce(pair.verifier, pair.challenge, method="S512")


class TestValidateCallbackParams:
    def test_accepts_matching_state_and_verifier(self):
        validate_callback_params(
            state="abc", expected_state="abc", code_verifier="v" * 43
        )

    def test_rejects_provider_error(self):
        with pytest.raises(HTTPException) as exc:
            validate_callback_params(
                state="abc",
                expected_state="abc",
                code_verifier="v" * 43,
                error="access_denied",
            )
        assert exc.value.status_code == 400
        assert "access_denied" in exc.value.detail

    def test_rejects_state_mismatch(self):
        with pytest.raises(HTTPException) as exc:
            validate_callback_params(
                state="attacker", expected_state="abc", code_verifier="v" * 43
            )
        assert exc.value.status_code == 400
        assert "state" in exc.value.detail.lower()

    def test_rejects_missing_state(self):
        with pytest.raises(HTTPException):
            validate_callback_params(
                state=None, expected_state="abc", code_verifier="v" * 43
            )

    def test_rejects_missing_expected_state(self):
        with pytest.raises(HTTPException) as exc:
            validate_callback_params(
                state="abc", expected_state=None, code_verifier="v" * 43
            )
        assert exc.value.status_code == 500

    def test_rejects_missing_verifier(self):
        with pytest.raises(HTTPException) as exc:
            validate_callback_params(state="abc", expected_state="abc", code_verifier=None)
        assert exc.value.status_code == 400
        assert "verifier" in exc.value.detail.lower()

    def test_error_takes_precedence_over_missing_state(self):
        with pytest.raises(HTTPException) as exc:
            validate_callback_params(
                state=None, expected_state=None, code_verifier=None, error="server_error"
            )
        assert "server_error" in exc.value.detail


class TestParseCallbackParams:
    def test_parses_single_values(self):
        parsed = parse_callback_params("code=abc&state=xyz")
        assert parsed == {"code": "abc", "state": "xyz"}

    def test_keeps_first_of_duplicates(self):
        assert parse_callback_params("state=a&state=b") == {"state": "a"}

    def test_preserves_blank_values(self):
        assert parse_callback_params("error=&error_description=nope") == {
            "error": "",
            "error_description": "nope",
        }
