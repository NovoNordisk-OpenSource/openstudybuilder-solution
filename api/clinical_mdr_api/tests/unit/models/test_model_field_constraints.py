"""Unit tests for response/request field constraints that keep the API's
documented OpenAPI types honest."""

from datetime import UTC, date, datetime

import pytest
from pydantic import ValidationError

from clinical_mdr_api.models.controlled_terminologies.ct_package import CTPackage
from clinical_mdr_api.models.standard_data_models.sponsor_model_schema import (
    SponsorModelSchemaCreateInput,
)
from common.config import settings


def _package(import_date: datetime) -> CTPackage:
    return CTPackage(
        uid="CTPackage_000001",
        catalogue_name="SDTM CT",
        name="SDTM CT 2020-03-27",
        description=None,
        registration_status=None,
        extends_package=None,
        import_date=import_date,
        effective_date=date(2020, 3, 27),
    )


class TestCTPackageImportDate:
    def test_naive_value_is_stamped_utc(self):
        # `import_date` is documented as `format: date-time`, which requires an
        # offset. Packages imported before import dates were stored with a
        # timezone hold a naive value in the database.
        package = _package(datetime(2020, 3, 27, 12, 30))
        assert package.import_date.tzinfo is not None
        assert package.import_date.utcoffset().total_seconds() == 0

    def test_aware_value_is_left_alone(self):
        aware = datetime(2020, 3, 27, 12, 30, tzinfo=UTC)
        assert _package(aware).import_date == aware


class TestSponsorModelSchemaVersion:
    def test_accepts_largest_value_neo4j_can_store(self):
        model = SponsorModelSchemaCreateInput(
            schema_version=settings.max_int_neo4j, schema="a: 1"
        )
        assert model.schema_version == settings.max_int_neo4j

    def test_rejects_value_wider_than_64_bits(self):
        # Larger values used to reach the database and crash the write with a 500.
        with pytest.raises(ValidationError, match="less_than_equal"):
            SponsorModelSchemaCreateInput(
                schema_version=settings.max_int_neo4j + 1, schema="a: 1"
            )
