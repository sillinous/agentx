"""
Tests for JWT Authentication Module
"""

import pytest
import os
import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException
from auth import (
    create_access_token,
    decode_access_token,
    extract_token_from_header,
    verify_user_access,
    TokenData,
)


class TestTokenCreation:
    def test_create_access_token_valid(self):
        """Test creating a valid access token"""
        user_id = "test-user-123"
        email = "test@example.com"
        subscription_tier = "enterprise"

        token = create_access_token(user_id, email, subscription_tier)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_contains_correct_claims(self):
        """Test that created token contains all required claims"""
        user_id = "test-user-123"
        email = "test@example.com"
        subscription_tier = "standard"

        token = create_access_token(user_id, email, subscription_tier)

        # Decode without verification to inspect payload
        secret = os.getenv("JWT_SECRET", "development-secret-key-change-in-production")
        payload = jwt.decode(token, secret, algorithms=["HS256"])

        assert payload["user_id"] == user_id
        assert payload["email"] == email
        assert payload["subscription_tier"] == subscription_tier
        assert payload["type"] == "access_token"
        assert "exp" in payload
        assert "iat" in payload


class TestTokenDecoding:
    def test_decode_valid_token(self):
        """Test decoding a valid token"""
        user_id = "test-user-456"
        email = "user@test.com"
        subscription_tier = "enterprise"

        token = create_access_token(user_id, email, subscription_tier)
        token_data = decode_access_token(token)

        assert token_data.user_id == user_id
        assert token_data.email == email
        assert token_data.subscription_tier == subscription_tier

    def test_decode_expired_token(self):
        """Test that expired tokens raise an exception"""
        # Create a token that expired 1 hour ago
        secret = os.getenv("JWT_SECRET", "development-secret-key-change-in-production")
        expiration = datetime.utcnow() - timedelta(hours=1)

        payload = {
            "user_id": "test-user",
            "email": "test@test.com",
            "subscription_tier": "standard",
            "exp": expiration,
            "iat": datetime.utcnow() - timedelta(hours=2),
            "type": "access_token",
        }

        expired_token = jwt.encode(payload, secret, algorithm="HS256")

        with pytest.raises(HTTPException) as exc_info:
            decode_access_token(expired_token)

        assert exc_info.value.status_code == 401
        assert "expired" in exc_info.value.detail.lower()

    def test_decode_invalid_token(self):
        """Test that invalid tokens raise an exception"""
        invalid_token = "not.a.valid.token"

        with pytest.raises(HTTPException) as exc_info:
            decode_access_token(invalid_token)

        assert exc_info.value.status_code == 401

    def test_decode_token_with_invalid_signature(self):
        """Test that tokens with invalid signatures raise an exception"""
        # Create a token with a different secret
        payload = {
            "user_id": "test-user",
            "email": "test@test.com",
            "subscription_tier": "standard",
            "exp": datetime.utcnow() + timedelta(hours=1),
            "iat": datetime.utcnow(),
            "type": "access_token",
        }

        tampered_token = jwt.encode(payload, "wrong-secret", algorithm="HS256")

        with pytest.raises(HTTPException) as exc_info:
            decode_access_token(tampered_token)

        assert exc_info.value.status_code == 401

    def test_decode_token_missing_user_id(self):
        """Test that tokens without user_id claim raise an exception"""
        secret = os.getenv("JWT_SECRET", "development-secret-key-change-in-production")
        payload = {
            "email": "test@test.com",
            "subscription_tier": "standard",
            "exp": datetime.utcnow() + timedelta(hours=1),
            "iat": datetime.utcnow(),
            "type": "access_token",
        }

        token = jwt.encode(payload, secret, algorithm="HS256")

        with pytest.raises(HTTPException) as exc_info:
            decode_access_token(token)

        assert exc_info.value.status_code == 401


class TestTokenExtraction:
    def test_extract_valid_bearer_token(self):
        """Test extracting token from valid Authorization header"""
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test.token"
        header = f"Bearer {token}"

        extracted = extract_token_from_header(header)

        assert extracted == token

    def test_extract_missing_bearer_prefix(self):
        """Test that headers without 'Bearer ' prefix raise an exception"""
        header = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test.token"

        with pytest.raises(HTTPException) as exc_info:
            extract_token_from_header(header)

        assert exc_info.value.status_code == 401

    def test_extract_empty_header(self):
        """Test that empty headers raise an exception"""
        with pytest.raises(HTTPException) as exc_info:
            extract_token_from_header("")

        assert exc_info.value.status_code == 401

    def test_extract_none_header(self):
        """Test that None headers raise an exception"""
        with pytest.raises(HTTPException) as exc_info:
            extract_token_from_header(None)

        assert exc_info.value.status_code == 401


class TestAccessVerification:
    def test_verify_standard_user_standard_resource(self):
        """Test standard user accessing standard resource"""
        token_data = TokenData(
            user_id="test-user",
            email="test@test.com",
            subscription_tier="standard",
        )

        assert verify_user_access(token_data, "standard") is True

    def test_verify_enterprise_user_standard_resource(self):
        """Test enterprise user accessing standard resource"""
        token_data = TokenData(
            user_id="test-user",
            email="test@test.com",
            subscription_tier="enterprise",
        )

        assert verify_user_access(token_data, "standard") is True

    def test_verify_standard_user_enterprise_resource(self):
        """Test standard user accessing enterprise resource (should fail)"""
        token_data = TokenData(
            user_id="test-user",
            email="test@test.com",
            subscription_tier="standard",
        )

        assert verify_user_access(token_data, "enterprise") is False

    def test_verify_enterprise_user_enterprise_resource(self):
        """Test enterprise user accessing enterprise resource"""
        token_data = TokenData(
            user_id="test-user",
            email="test@test.com",
            subscription_tier="enterprise",
        )

        assert verify_user_access(token_data, "enterprise") is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
