from starlette.testclient import TestClient

from clinical_mdr_api import main

test_client = TestClient(main.app)
