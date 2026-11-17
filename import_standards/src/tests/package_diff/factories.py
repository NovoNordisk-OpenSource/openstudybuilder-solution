"""Builders for raw CDISC CT package dicts used across the package_diff tests.

Extracted from test_ct_diff.py when the grouping and site-rendering modules
arrived and needed the same shapes: three test modules building package
literals by hand would drift apart.

These return the *raw* JSON shape, exactly as a downloaded package looks. Pass
them through ``ct_diff.normalize_package`` to get the internal form.
"""


def make_term(concept_id, submission_value, definition="A definition.", **kwargs):
    term = {
        "conceptId": concept_id,
        "definition": definition,
        "preferredTerm": f"{concept_id} preferred term",
        "submissionValue": submission_value,
    }
    term.update(kwargs)
    return term


def make_codelist(concept_id, submission_value, terms, **kwargs):
    codelist = {
        "conceptId": concept_id,
        "name": f"{concept_id} name",
        "definition": "A codelist definition.",
        "preferredTerm": f"{concept_id} preferred term",
        "submissionValue": submission_value,
        "extensible": "false",
        "synonyms": [],
        "terms": terms,
    }
    codelist.update(kwargs)
    return codelist


def make_package(effective_date, codelists, name="SDTM CT"):
    return {
        "name": f"{name} {effective_date}",
        "effectiveDate": effective_date,
        "version": effective_date,
        "codelists": codelists,
    }
