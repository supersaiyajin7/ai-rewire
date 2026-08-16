import os
import jwt
from jwt import PyJWKClient
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Read Keycloak settings from environment variables
KEYCLOAK_DOMAIN = os.getenv("KEYCLOAK_DOMAIN", "http://keycloak:8080")
REALM_NAME = os.getenv("KEYCLOAK_REALM", "my-platform")

# Keycloak OpenID Connect Certificate Endpoint
KEYCLOAK_ISSUER = f"{KEYCLOAK_DOMAIN}/realms/{REALM_NAME}"
JWKS_URL = f"{KEYCLOAK_ISSUER}/protocol/openid-connect/certs"

jwk_client = PyJWKClient(JWKS_URL)
security = HTTPBearer()

def verify_jwt_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    """
    Validates incoming OAuth2 JWT tokens against Keycloak's public keys.
    Returns decoded token payload if valid; raises HTTP 401 if expired or invalid.
    """
    token = credentials.credentials
    try:
        # Fetch the matching signing key from Keycloak JWKS
        signing_key = jwk_client.get_signing_key_from_jwt(token)

        # Decode & Verify RS256 Signature
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={"verify_aud": False}
        )
        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please request a new token from Keycloak."
        )
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {str(e)}"
        )
