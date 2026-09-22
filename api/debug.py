import os
import sys

from uvicorn.main import main

if __name__ == "__main__":
    sys.argv.append("clinical_mdr_api.main:app")

    os.environ.setdefault("UVICORN_HOST", "127.0.0.1")
    os.environ.setdefault("UVICORN_PORT", "8000")
    os.environ.setdefault("UVICORN_RELOAD", "true")

    # pylint: disable=no-value-for-parameter
    sys.exit(main())
