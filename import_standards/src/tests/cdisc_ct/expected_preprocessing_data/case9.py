from mdr_standards_import.scripts.load_ct_preprocessing import Term, Codelist
from src.tests.cdisc_ct.test_pipeline import Package, Import, Log


def get_expected_imports(effective_date, author_id):
    term1_a = Term(
        uid=f"{effective_date}_T1_sv-T1-1",
        concept_id="T1_sv-T1-1",
        code_submission_value="sv-T1-1",
        name_submission_value=None,
        submission_value=None,
        preferred_term="PT T1",
        definition="Definition T1",
        synonyms=None,
    )

    term1_b = Term(
        uid=f"{effective_date}_T1_sv-T1-2",
        concept_id="T1_sv-T1-2",
        code_submission_value="sv-T1-2",
        name_submission_value=None,
        submission_value=None,
        preferred_term="PT T1",
        definition="Definition T1",
        synonyms=None,
    )

    codelist1 = Codelist(
        uid=f"{effective_date}_C1A",
        concept_id="C1A",
        name="Codelist 1A",
        submission_value="SV",
        preferred_term="PT 1A",
        definition="Definition 1A",
        extensible=True,
        synonyms=None,
        terms=[term1_a],
    )

    codelist2 = Codelist(
        uid=f"{effective_date}_C1B",
        concept_id="C1B",
        name="Codelist 1B",
        submission_value="SV",
        preferred_term="PT 1B",
        definition="Definition 1B",
        extensible=True,
        synonyms=None,
        terms=[term1_b],
    )

    package1 = Package(
        uid=f"{effective_date}_TEST-CASE 9 CT",
        catalogue_name="TEST-CASE 9 CT",
        registration_status="Testing",
        name="TEST-CASE 9 CT 2020-01-01",
        label="Test-Case 9 Controlled Terminology Package 1 Effective 2020-01-01",
        description="Test-Case 9: no differentiation for the submission values possible -> use each as code submission value.",
        source="Test source",
        href="/mdr/ct/packages/cat9-2020-01-01",
        terms=[term1_a, term1_b],
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
