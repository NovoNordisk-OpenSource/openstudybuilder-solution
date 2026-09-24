from os import environ

import requests


def get_token():
    """Returns authentication token"""
    client_id = environ.get("CLIENT_ID", "")
    if client_id:
        client_secret = environ.get("CLIENT_SECRET")
        token_endpoint = environ.get("TOKEN_ENDPOINT")
        scope = environ.get("SCOPE")
        response = requests.post(
            token_endpoint,
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "grant_type": "client_credentials",
                "scope": scope,
            },
            timeout=30,
            verify=False,
        )
        response.raise_for_status()
        payload = response.json()
        access_token = payload.get("access_token")
        if not access_token:
            msg = "missing access token from token payload"
            raise RuntimeError(msg)
        if not access_token:
            msg = "missing token type from token payload"
            raise RuntimeError(msg)
        return access_token
    return None


if __name__ == "__main__":
    print(get_token())
