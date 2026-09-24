from mdr_standards_import.scripts.load_ct_preprocessing import Term, Codelist
from src.tests.cdisc_ct.test_pipeline import Package, Import


def get_expected_imports(effective_date, author_id):
    term1 = Term(
        uid=f"{effective_date}_T1",
        concept_id="T1",
        code_submission_value="code-T1",
        name_submission_value="name-T1",
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
        definition="Definition 1A; goes together with 1B; differentiation via codelist submission values",
        extensible=True,
        synonyms=None,
        terms=[term1],
    )

    codelist2 = Codelist(
        uid=f"{effective_date}_C1B",
        concept_id="C1B",
        name="Codelist 1B",
        submission_value="SV CD",
        preferred_term="PT 1B",
        definition="Definition 1B; goes together with 1A; differentiation via codelist submission values",
        extensible=True,
        synonyms=None,
        terms=[term1],
    )

    term2 = Term(
        uid=f"{effective_date}_T2",
        concept_id="T2",
        code_submission_value="code-T2",
        name_submission_value="name-T2",
        submission_value=None,
        preferred_term="PT T2",
        definition="Definition T2",
        synonyms=None,
    )

    codelist3 = Codelist(
        uid=f"{effective_date}_C2A",
        concept_id="C2A",
        name="Codelist 2A",
        submission_value="SV",
        preferred_term="PT 2A",
        definition="Definition 2A; goes together with 2B; differentiation via codelist submission values",
        extensible=True,
        synonyms=None,
        terms=[term2],
    )

    codelist4 = Codelist(
        uid=f"{effective_date}_C2B",
        concept_id="C2B",
        name="Codelist 2B",
        submission_value="SVCD",
        preferred_term="PT 2B",
        definition="Definition 2B; goes together with 2A; differentiation via codelist submission values",
        extensible=True,
        synonyms=None,
        terms=[term2],
    )

    term3 = Term(
        uid=f"{effective_date}_T3-1",
        concept_id="T3-1",
        code_submission_value="code-T3-1",
        name_submission_value="name-T3-1",
        submission_value=None,
        preferred_term="PT T3-1",
        definition="Definition T3-1",
        synonyms=None,
    )
    term4 = Term(
        uid=f"{effective_date}_T3-2",
        concept_id="T3-2",
        code_submission_value="code-T3-2",
        name_submission_value="name-T3-2",
        submission_value=None,
        preferred_term="PT T3-2",
        definition="Definition T3-2",
        synonyms=None,
    )
    codelist5 = Codelist(
        uid=f"{effective_date}_C3B",
        concept_id="C3B",
        name="Codelist 3B",
        submission_value="SVCD",
        preferred_term="PT 3B",
        definition="Definition 3B; goes together with C3A; differentiation via codelist submission values",
        extensible=True,
        synonyms=None,
        terms=[term3, term4],
    )
    codelist6 = Codelist(
        uid=f"{effective_date}_C3A",
        concept_id="C3A",
        name="Codelist 3A",
        submission_value="SV",
        preferred_term="PT 3A",
        definition="Definition 3A; goes together with C3B; differentiation via codelist submission values",
        extensible=True,
        synonyms=None,
        terms=[term3, term4],
    )

    package1 = Package(
        uid=f"{effective_date}_TEST-CASE 7 CT",
        catalogue_name="TEST-CASE 7 CT",
        registration_status="Final",
        name="TEST-CASE 7 CT 2020-01-01",
        label="Test-Case 7 Controlled Terminology Package 1 Effective 2020-01-01",
        description="Test-Case 7: There is a codelist with the name 'Codelist 001' and another codelist with the name 'Codelist 002'. -> import code and name submission values and log as inconsistency.",
        source="Test source",
        href="/mdr/ct/packages/cat7-2020-01-01",
        terms=[term1, term2, term3, term4],
        codelists=[codelist1, codelist2, codelist3, codelist4, codelist6, codelist5],
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
