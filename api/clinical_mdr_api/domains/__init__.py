# Disable the pydantic warning for fields starting with an underscore.
import warnings

warnings.filterwarnings(
    "ignore", message="fields may not start with an underscore, ignoring.*"
)
