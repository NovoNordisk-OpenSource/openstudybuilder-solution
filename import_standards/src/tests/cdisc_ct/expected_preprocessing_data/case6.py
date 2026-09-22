from mdr_standards_import.scripts.load_ct_preprocessing import Term, Codelist
from src.tests.cdisc_ct.test_pipeline import Package, Import


def get_expected_imports(effective_date, author_id):
    term1 = Term(
        uid=f"{effective_date}_T001",
        concept_id="T001",
        code_submission_value="code-SMT001",
        name_submission_value="name-SMT001",
        submission_value=None,
        preferred_term="PT T001",
        definition="Definition T001",
        synonyms=None,
    )

    codelist1 = Codelist(
        uid=f"{effective_date}_C001",
        concept_id="C001",
        name="Codelist 001 Code",
        submission_value="SMN001",
        preferred_term="PT C001",
        definition="Definition C001; goes together with C002",
        extensible=True,
        synonyms=None,
        terms=[term1],
    )

    codelist2 = Codelist(
        uid=f"{effective_date}_C002",
        concept_id="C002",
        name="Codelist 001",
        submission_value="SMN002",
        preferred_term="PT C002",
        definition="Definition C002; goes together with C001",
        extensible=True,
        synonyms=None,
        terms=[term1],
    )

    package1 = Package(
        uid=f"{effective_date}_TEST-CASE 6 CT",
        catalogue_name="TEST-CASE 6 CT",
        registration_status="Final",
        name="TEST-CASE 6 CT 2020-01-01",
        label="Test-Case 6 Controlled Terminology Package 1 Effective 2020-01-01",
        description="Test-Case 6: There is a codelist with the name 'Codelist 001 Code' and another codelist with the name 'Codelist 001'. -> import code and name submission values.",
        source="Test source",
        href="/mdr/ct/packages/cat6-2020-01-01",
        terms=[term1],
        codelists=[codelist1, codelist2],
        discontinued_codelists=[],
    )

    import1 = Import(
        effective_date=effective_date,
        author_id=author_id,
        packages=[package1],
        discontinued_codelists=[],
        log_entries=[],
    )

    return [import1]
