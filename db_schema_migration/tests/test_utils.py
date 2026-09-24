import pytest

from migrations.utils import utils


@pytest.mark.parametrize(
    "input_val, output",
    [
        pytest.param(
            "japaneseTrialRegistryIdJapicNullValueCode",
            "japanese_trial_registry_id_japic_null_value_code",
        ),
        pytest.param(
            "japanese_trial_registry_id_JAPIC_null_value_code",
            "japanese_trial_registry_id_japic_null_value_code",
        ),
        pytest.param(
            "id_metadata.registry_identifiers",
            "id_metadata.registry_identifiers",
        ),
    ],
)
def test_snake_case(input_val, output):
    assert output == utils.snake_case(input_val)
