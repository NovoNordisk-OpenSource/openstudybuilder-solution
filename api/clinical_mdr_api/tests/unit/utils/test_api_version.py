from deepdiff import DeepDiff

from clinical_mdr_api.utils import api_version as utils


def test_compare_versions():
    assert utils.compare_versions("1.0.1", "1.0.2") == -1
    assert utils.compare_versions("1.0.1", "1.1.0") == -1
    assert utils.compare_versions("1.0.1", "2.0.0") == -1
    assert utils.compare_versions("1.0.1", "1.0.1") == 0
    assert utils.compare_versions("1.0.1", "1.0.0") == 1

    assert utils.compare_versions("1.5.1", "1.7.0") == -1
    assert utils.compare_versions("1.5.1", "1.5.1") == 0
    assert utils.compare_versions("1.5.1", "1.3.2") == 1

    assert utils.compare_versions("2.0.1", "2.0.2") == -1
    assert utils.compare_versions("2.0.1", "2.0.1") == 0
    assert utils.compare_versions("2.0.1", "2.0.0") == 1


def test_increment_version_number():
    assert utils.increment_version_number("1.0.0") == "1.0.1"
    assert utils.increment_version_number("1.3.6") == "1.3.7"
    assert utils.increment_version_number("2.0.5") == "2.0.6"


def test_increment_api_version_if_needed():
    # API spec changed => version should be auto-increment
    api_spec_new = {
        "openapi": "3.0.2",
        "info": {"title": "OpenStudyBuilder API", "version": "2.0.0"},
        "paths": {"/odms/study-events": {}},
    }
    api_spec_old = {
        "openapi": "3.0.2",
        "info": {"title": "OpenStudyBuilder API", "version": "2.0.0"},
        "paths": {"/odms/study-events-old": {}},
    }

    api_spec_final = utils.increment_api_version_if_needed(api_spec_new, api_spec_old)
    assert api_spec_final["info"]["version"] == "2.0.1"
    assert not DeepDiff(
        api_spec_new,
        api_spec_final,
        exclude_paths={
            "root['info']",
        },
    )

    # API spec changed, version already manually incremented => no need for auto-increment
    api_spec_new = {
        "openapi": "3.0.2",
        "info": {"title": "OpenStudyBuilder API", "version": "2.0.2"},
        "paths": {"/odms/study-events": {}},
    }
    api_spec_old = {
        "openapi": "3.0.2",
        "info": {"title": "OpenStudyBuilder API", "version": "2.0.0"},
        "paths": {"/odms/study-events-old": {}},
    }

    api_spec_final = utils.increment_api_version_if_needed(api_spec_new, api_spec_old)
    assert api_spec_final["info"]["version"] == "2.0.2"
    assert not DeepDiff(api_spec_new, api_spec_final)

    # API spec not changed => no need for auto-increment
    api_spec_new = {
        "openapi": "3.0.2",
        "info": {"title": "OpenStudyBuilder API", "version": "2.0.0"},
        "paths": {"/odms/study-events": {}},
    }
    api_spec_old = {
        "openapi": "3.0.2",
        "info": {"title": "OpenStudyBuilder API", "version": "2.0.0"},
        "paths": {"/odms/study-events": {}},
    }

    api_spec_final = utils.increment_api_version_if_needed(api_spec_new, api_spec_old)
    assert api_spec_final["info"]["version"] == "2.0.0"
    assert not DeepDiff(api_spec_new, api_spec_final)
