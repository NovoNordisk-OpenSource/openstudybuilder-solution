import ssl
import httpx
import httpx_auth
from os import environ
import os
import logging
import sys
import json

OUTPUT_DIR = environ.get("OUTPUT_DIR", "./output")
LOG_LEVEL = environ.get("LOG_LEVEL", "INFO")

DEFAULT_QUERY_PARAMS = {
    "page_size": 0,
    "page_number": 1,
}

# ---------------------------------------------------------------
# Api bindings
# ---------------------------------------------------------------
#
class StudyExporter:
    def __init__(self):
        numeric_level = getattr(logging, LOG_LEVEL.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError("Invalid log level: %s" % LOG_LEVEL)
        logging.basicConfig(
            level=numeric_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        self.log = logging.getLogger("studybuilder_export")
        self.api_base_url = self._read_env("API_BASE_URL")
        self._create_httpx_client()
        self.verify_connection()

    def _read_env(self, varname):
        value = environ.get(varname)
        if not value:
            msg = f"missing {varname} env variable"
            self.log.error(msg)
            raise RuntimeError(msg)
        return value

    def _create_httpx_client(self):
        """
        Creates the HTTPX client with the appropriate authentication method
        based on the environment variables.
        """
        client_id = environ.get("CLIENT_ID", "")
        scope = environ.get("SCOPE", "")
        token_endpoint = environ.get("TOKEN_ENDPOINT", "")
        auth_endpoint = environ.get("AUTH_ENDPOINT", "")
        client_secret = environ.get("CLIENT_SECRET", "")

        # HTTPX doesn't automatically use the REQUESTS_CA_BUNDLE environment variable
        ca_bundle = os.environ.get("REQUESTS_CA_BUNDLE", "")
        if ca_bundle:
            context = ssl.create_default_context(
                cafile=ca_bundle
            )
        else:
            context = None

        if not client_id:
            self.log.info("No CLIENT_ID provided, running without authentication")
            auth = None
        elif client_secret:
            self.log.info("CLIENT_ID and CLIENT_SECRET provided, enabling authentication")
            auth = httpx_auth.OAuth2ClientCredentials(
                token_url=token_endpoint,
                client_id=client_id,
                client_secret=client_secret,
                scope=scope,
            )
        else:
            self.log.info("CLIENT_ID provided without CLIENT_SECRET, using interactive authentication")
            auth = httpx_auth.OAuth2AuthorizationCodePKCE(
                authorization_url=auth_endpoint,
                token_url=token_endpoint,
                client_id=client_id,
                scope=scope,
            )
        self.client = httpx.Client(base_url=self.api_base_url, auth=auth, verify=context, timeout=60)


    # ---------------------------------------------------------------
    # Verify connection to api (and database)
    # ---------------------------------------------------------------
    #
    # Verify that Clinical MDR API is online
    # TODO Replace with api health check resource ...
    def verify_connection(self):
        try:
            response = self.client.get("/libraries")
            response.raise_for_status()
            self.log.info(f"Connected to api at {self.api_base_url}")
        except Exception as e:
            self.log.error(
                f"Failed to connect to backend, is it running?\nError was:\n{e}"
            )
            sys.exit(1)

    def get_csv_from_api(self, path):
        page_params = {
            "page_number": 1,
            "page_size": 0,
        }
        headers = {
            "Accept": "text/csv",
        }
        response = self.client.get(path, params=page_params, headers=headers)
        if response.is_success:
            self.log.info(f"Successfully fetched CSV data from: {path}")
            return response.text
        else:
            if "message" in response.json():
                self.log.error("get %s %s", path, response.json()["message"])
            else:
                self.log.error("get %s %s", path, response.text)
            return None


    def save_csv(self, data, dir, filename):
        path = os.path.join(dir, filename)
        with open(path, "w") as f:
            self.log.info(f"Saving to file: {path}")
            f.write(data)


def run_export():
    try:
        os.mkdir("output")
    except FileExistsError:
        pass
    api = StudyExporter()


    # Studies
    api.log.info("=== Export studies ===")
    studies = api.get_csv_from_api("/studies")
    api.save_csv(studies, OUTPUT_DIR, "studies.csv")

    # All done
    api.log.info(f"=== Export completed successfully ===")


if __name__ == "__main__":
    run_export()
