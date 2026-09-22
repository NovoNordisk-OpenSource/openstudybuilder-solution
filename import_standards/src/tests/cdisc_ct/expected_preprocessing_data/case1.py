from mdr_standards_import.scripts.load_ct_preprocessing import Term, Codelist
from src.tests.cdisc_ct.test_pipeline import Package, Import


def get_expected_imports(effective_date, author_id):
    term1 = Term(
        uid=f"{effective_date}_T001",
        concept_id="T001",
        code_submission_value="code-SMT001",
        name_submission_value=None,
        submission_value=None,
        preferred_term="PT T001",
        definition="Definition T001",
        synonyms=["Synonym 1", "Synonym 2"],
    )

    codelist1 = Codelist(
        uid=f"{effective_date}_C001",
        concept_id="C001",
        name="Codelist 001",
        submission_value="SMN001",
        preferred_term="PT C001",
        definition="Definition C001",
        extensible=True,
        synonyms=["Analysis Purpose"],
        terms=[term1],
    )

    package1 = Package(
        uid=f"{effective_date}_TEST-CASE 1 CT",
        catalogue_name="TEST-CASE 1 CT",
        registration_status="Final",
        name="TEST-CASE 1 CT 2020-01-01",
        label="Test-Case 1 Controlled Terminology Package 1 Effective 2020-01-01",
        description="Test-Case 1: Only 'Codelist 001' without another codelist. -> import as code_submission_value; no inconsistency.",
        source="Test source",
        href="/mdr/ct/packages/case1-2020-01-01",
        terms=[term1],
        codelists=[codelist1],
        discontinued_codelists=[],
    )
    import1 = Import(
        effective_date,
        author_id,
        packages=[package1],
        discontinued_codelists=[],
        log_entries=[],
    )

    return [import1]
