"""Unit tests for the ``preserve_whitespace`` opt-out on ``InputModel``.

``InputModel`` strips surrounding whitespace from every string field by default.
A field may opt out via ``json_schema_extra={"preserve_whitespace": True}`` so an
opaque blob (e.g. the Sponsor Model Schema YAML text) is stored byte-for-byte.
The verbatim guarantee is what makes content-hash idempotency stable, so it is
worth pinning directly.
"""

from typing import Annotated

from pydantic import Field

from clinical_mdr_api.domains.standard_data_models.sponsor_model_schema import (
    SponsorModelSchemaVO,
)
from clinical_mdr_api.models.standard_data_models.sponsor_model_schema import (
    SponsorModelSchemaCreateInput,
)
from clinical_mdr_api.models.utils import InputModel


class _Sample(InputModel):
    stripped: Annotated[str | None, Field()] = None
    verbatim: Annotated[
        str | None,
        Field(json_schema_extra={"preserve_whitespace": True}),
    ] = None


class TestPreserveWhitespace:
    def test_default_field_is_stripped(self):
        model = _Sample(stripped="  hello  \n")
        assert model.stripped == "hello"

    def test_opted_out_field_is_preserved_verbatim(self):
        blob = "  fields:\n    - name: X\n  \n"
        model = _Sample(verbatim=blob)
        assert model.verbatim == blob

    def test_opt_out_does_not_leak_to_sibling_fields(self):
        model = _Sample(stripped="  a  ", verbatim="  b  ")
        assert model.stripped == "a"
        assert model.verbatim == "  b  "


class TestSchemaCreateInputPreservesBlob:
    def test_schema_content_is_kept_byte_for_byte(self):
        # Leading/trailing whitespace and a trailing newline must survive so the
        # stored blob round-trips exactly as submitted.
        raw = "\nfields:\n  - name: STUDYID\n    transformer: identity\n  \n"
        model = SponsorModelSchemaCreateInput(schema_version=1, schema=raw)
        assert model.schema_content == raw

    def test_content_hash_is_stable_across_identical_submissions(self):
        # Two identical submissions must hash the same; this is the idempotency
        # guarantee the verbatim storage exists to protect.
        raw = "  fields:\n  - name: STUDYID\n  "
        first = SponsorModelSchemaCreateInput(schema_version=1, schema=raw)
        second = SponsorModelSchemaCreateInput(schema_version=1, schema=raw)
        assert SponsorModelSchemaVO.compute_content_hash(
            first.schema_content
        ) == SponsorModelSchemaVO.compute_content_hash(second.schema_content)

    def test_whitespace_difference_changes_the_content_hash(self):
        # Because whitespace is preserved, a whitespace-only edit is a real content
        # change (not an idempotent no-op).
        a = SponsorModelSchemaVO.compute_content_hash("fields: []")
        b = SponsorModelSchemaVO.compute_content_hash("fields: []\n")
        assert a != b
