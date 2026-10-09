def assert_url(value, message):
    """Assert value is URL"""

    __tracebackhide__ = True

    assert value, f"{message}: empty"
    assert "://" in value, f"{message}: no :// in URL"


def assert_https_url(value, message):
    """Assert value is URL starts with 'https://'"""

    __tracebackhide__ = True

    assert_url(value, message)
    assert value.lower().startswith(
        "https://"
    ), f"{message}: URL doesn't start with https://"
