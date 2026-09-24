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
        synonyms=["Synonym 1", "Synonym 2"],
    )

    codelist1 = Codelist(
        uid=f"{effective_date}_C001",
        concept_id="C001",
        name="Codelist 001 Code",
        submission_value="SMN001",
        preferred_term="PT C001",
        definition="Definition C001; goes together with C002",
        extensible=True,
        synonyms=["Analysis Purpose"],
        terms=[term1],
    )

    codelist2 = Codelist(
        uid=f"{effective_date}_C002",
        concept_id="C002",
        name="Codelist 001 Name",
        submission_value="SMN002",
        preferred_term="PT C002",
        definition="Definition C002; goes together with C001",
        extensible=True,
        synonyms=["Analysis Purpose"],
        terms=[term1],
    )

    term3 = Term(
        uid=f"{effective_date}_T003",
        concept_id="T003",
        code_submission_value="code-SMT003",
        name_submission_value="name-SMT003",
        submission_value=None,
        preferred_term="PT T003",
        definition="Definition T003",
        synonyms=None,
    )

    codelist3 = Codelist(
        uid=f"{effective_date}_C003",
        concept_id="C003",
        name="Codelist 003 Name",
        submission_value="SMN003",
        preferred_term="PT C003",
        definition="Definition C003; goes together with C004",
        extensible=True,
        synonyms=[],
        terms=[term3],
    )

    codelist4 = Codelist(
        uid=f"{effective_date}_C004",
        concept_id="C004",
        name="Codelist 003 Code",
        submission_value="SMN003",
        preferred_term="PT C004",
        definition="Definition C004; goes together with C003",
        extensible=True,
        synonyms=[],
        terms=[term3],
    )

    package1 = Package(
        uid=f"{effective_date}_TEST-CASE 2 CT",
        catalogue_name="TEST-CASE 2 CT",
        registration_status="Final",
        name="TEST-CASE 2 CT 2020-01-01",
        label="Test-Case 2 Controlled Terminology Package 1 Effective 2020-01-01",
        description="Test-Case 2: There is a codelist with the name 'Codelist 001 Name' and another codelist with the name 'Codelist 001 Code'. -> standard case; no inconsistency",
        source="Test source",
        href="/mdr/ct/packages/cat2-2020-01-01",
        terms=[term1, term3],
        codelists=[codelist1, codelist2, codelist3, codelist4],
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
