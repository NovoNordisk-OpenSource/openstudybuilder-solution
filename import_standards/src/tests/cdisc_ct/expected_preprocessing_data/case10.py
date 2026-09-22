from mdr_standards_import.scripts.load_ct_preprocessing import Term, Codelist
from src.tests.cdisc_ct.test_pipeline import Package, Import, Log


def get_expected_imports(effective_date, author_id):
    term1 = Term(
        uid=f"{effective_date}_T01",
        concept_id="T01",
        code_submission_value="code-T01",
        name_submission_value="name-T01",
        submission_value=None,
        preferred_term="PT T01",
        definition="Definition T01",
        synonyms=["Synonym 1", "Synonym 2"],
    )

    term2 = Term(
        uid=f"{effective_date}_T02",
        concept_id="T02",
        code_submission_value="code-T02",
        name_submission_value="name-T02",
        submission_value=None,
        preferred_term="PT T02",
        definition="Definition T02",
        synonyms=None,
    )

    codelist3 = Codelist(
        uid=f"{effective_date}_C03",
        concept_id="C03",
        name="Codelist XX Code",
        submission_value="SM C03",
        preferred_term="PT C03",
        definition="Definition C03",
        extensible=True,
        synonyms=["Analysis Purpose"],
        terms=[term1, term2],
    )

    codelist2 = Codelist(
        uid=f"{effective_date}_C02",
        concept_id="C02",
        name="Codelist XX Name",
        submission_value="SM C02",
        preferred_term="PT C02",
        definition="Definition C02",
        extensible=True,
        synonyms=["Analysis Purpose"],
        terms=[term1, term2],
    )

    # Terms of codelist C02 are inconsistent
    warning1 = Log(
        level="Warning",
        tagline="inconsistent terms",
        message="",
        affected_uid=f"{effective_date}_C02",
    )

    package1 = Package(
        uid=f"{effective_date}_CAT1 CT",
        catalogue_name="CAT1 CT",
        registration_status="Some Other Status",
        name="CAT1 CT 2020-01-01",
        label="Cat1 Controlled Terminology Package 1 Effective 2020-01-01",
        description="Terms of codelist C02 are inconsistent (cf. cat2-2020-01-01)",
        source="Cat1 source",
        href="/mdr/ct/packages/cat1-2020-01-01",
        terms=[term1, term2],
        codelists=[codelist2, codelist3],
        discontinued_codelists=[],
    )

    codelist1 = Codelist(
        uid=f"{effective_date}_C01",
        concept_id="C01",
        name="Codelist XX Code",
        submission_value="SM C01",
        preferred_term="PT C01",
        definition="Definition C01",
        extensible=True,
        synonyms=["Analysis Purpose"],
        terms=[term1],
    )

    package2 = Package(
        uid=f"{effective_date}_CAT2 CT",
        catalogue_name="CAT2 CT",
        registration_status="Final",
        name="CAT2 CT 2020-01-01",
        label="Cat2 Controlled Terminology Package 1 Effective 2020-01-01",
        description="Terms of codelist C02 are inconsistent (cf. Cat1-2020-01-01)",
        source="Cat2 source",
        href="/mdr/ct/packages/cat2-2020-01-01",
        terms=[term1],
        codelists=[codelist1, codelist2],
        discontinued_codelists=[],
    )

    term3 = Term(
        uid=f"{effective_date}_T03",
        concept_id="T03",
        code_submission_value=None,
        name_submission_value=None,
        submission_value=None,
        preferred_term="PT T03",
        definition="Definition T03",
        synonyms=["Synonym 1", "Synonym 2"],
    )

    term4 = Term(
        uid=f"{effective_date}_T04",
        concept_id="T04",
        code_submission_value="name-T04",
        name_submission_value=None,
        submission_value=None,
        preferred_term="PT T04",
        definition="Definition T04",
        synonyms=None,
    )

    term5 = Term(
        uid=f"{effective_date}_T05",
        concept_id="T05",
        code_submission_value="name-T05",
        name_submission_value=None,
        submission_value=None,
        preferred_term="PT T05",
        definition="Definition T05",
        synonyms=None,
    )

    term6 = Term(
        uid=f"{effective_date}_T06",
        concept_id="T06",
        code_submission_value="name-T06",
        name_submission_value=None,
        submission_value=None,
        preferred_term="PT T06",
        definition="Definition T06",
        synonyms=None,
    )

    codelist4 = Codelist(
        uid=f"{effective_date}_C04",
        concept_id="C04",
        name="Codelist C04",
        submission_value="SM C04",
        preferred_term="PT C04",
        definition="Definition C04",
        extensible=True,
        synonyms=["C04 X"],
        terms=[term3],
    )

    codelist5 = Codelist(
        uid=f"{effective_date}_C05",
        concept_id="C05",
        name="Codelist C05 NAME",
        submission_value="SM C05",
        preferred_term="PT C05",
        definition="Definition C05",
        extensible=True,
        synonyms=None,
        terms=[term4],
    )

    codelist6 = Codelist(
        uid=f"{effective_date}_C06",
        concept_id="C06",
        name="Codelist C06 coDe",
        submission_value="SM C06",
        preferred_term="PT C06",
        definition="Definition C06",
        extensible=True,
        synonyms=None,
        terms=[term5, term6],
    )

    term7_a = Term(
        uid=f"{effective_date}_T07_name-T07",
        concept_id="T07_name-T07",
        code_submission_value="name-T07",
        name_submission_value=None,
        submission_value=None,
        preferred_term="PT T07",
        definition="Definition T07",
        synonyms=None,
    )

    term7_b = Term(
        uid=f"{effective_date}_T07_code-T07",
        concept_id="T07_code-T07",
        code_submission_value="code-T07",
        name_submission_value=None,
        submission_value=None,
        preferred_term="PT T07",
        definition="Definition T07",
        synonyms=None,
    )

    codelist7 = Codelist(
        uid=f"{effective_date}_C07",
        concept_id="C07",
        name="Codelist C07",
        submission_value="SM C07",
        preferred_term="PT C07",
        definition="Definition C07",
        extensible=True,
        synonyms=None,
        terms=[term7_a],
    )

    codelist8 = Codelist(
        uid=f"{effective_date}_C08",
        concept_id="C08",
        name="Codelist C08",
        submission_value="SM C08",
        preferred_term="PT C08",
        definition="Definition C08",
        extensible=True,
        synonyms=None,
        terms=[term7_b],
    )

    # T03 has no submission value: -> log inconsistency
    warning2 = Log(
        level="Warning",
        tagline="no term submission value",
        message="",
        affected_uid=f"{effective_date}_T03",
    )

    info1 = Log(
        level="Info",
        tagline="unexpected codelist name",
        message="",
        affected_uid=f"{effective_date}_C05",
    )

    info2 = Log(
        level="Info",
        tagline="unexpected codelist name",
        message="",
        affected_uid=f"{effective_date}_C06",
    )

    package3 = Package(
        uid=f"{effective_date}_CAT3 CT",
        catalogue_name="CAT3 CT",
        registration_status="Final",
        name="CAT3 CT 2020-01-01",
        label="Cat3 Controlled Terminology Package 1 Effective 2020-01-01",
        description="T03 has no submission value: -> log inconsistency",
        source="Cat3 source",
        href="/mdr/ct/packages/cat3-2020-01-01",
        terms=[term3, term4, term5, term6],
        codelists=[codelist4, codelist5, codelist6],
        discontinued_codelists=[],
    )

    package4 = Package(
        uid=f"{effective_date}_CAT4 CT",
        catalogue_name="CAT4 CT",
        registration_status="Final",
        name="CAT4 CT 2020-01-01",
        label="Cat4 Controlled Terminology Package 1 Effective 2020-01-01",
        description="The codelists C07 and C08 have the same term, however we don't know how to differentiate between code- and name-submission-value: -> log inconsistency",
        source="Cat4 source",
        href="/mdr/ct/packages/cat4-2020-01-01",
        terms=[term7_b, term7_a],
        codelists=[codelist7, codelist8],
        discontinued_codelists=[],
    )

    warning4 = Log(
        level="Warning",
        tagline="no codelists defined",
        message="",
        affected_uid="2020-01-01_CAT5 CT",
    )

    package5 = Package(
        uid=f"{effective_date}_CAT5 CT",
        catalogue_name="CAT5 CT",
        registration_status="Final",
        name="CAT5 CT 2020-01-01",
        label="Cat5 Controlled Terminology Package 1 Effective 2020-01-01",
        description="No codelists defined -> log inconsistency",
        source="Cat5 source",
        href="/mdr/ct/packages/cat5-2020-01-01",
        terms=[],
        codelists=[],
        discontinued_codelists=[],
    )

    term8_a = Term(
        uid=f"{effective_date}_T08_name-T08",
        concept_id="T08_name-T08",
        code_submission_value="name-T08",
        name_submission_value=None,
        submission_value=None,
        preferred_term="PT T08",
        definition="Definition T08",
        synonyms=None,
    )

    term8_b = Term(
        uid=f"{effective_date}_T08_code-T08",
        concept_id="T08_code-T08",
        code_submission_value="code-T08",
        name_submission_value=None,
        submission_value=None,
        preferred_term="PT T08",
        definition="Definition T08",
        synonyms=None,
    )

    term8_c = Term(
        uid=f"{effective_date}_T08_unknown-future-T08",
        concept_id="T08_unknown-future-T08",
        code_submission_value="unknown-future-T08",
        name_submission_value=None,
        submission_value=None,
        preferred_term="PT T08",
        definition="Definition T08",
        synonyms=None,
    )

    codelist9 = Codelist(
        uid=f"{effective_date}_C09",
        concept_id="C09",
        name="Codelist C09",
        submission_value="SM C09",
        preferred_term="PT C09",
        definition="Definition C09",
        extensible=True,
        synonyms=None,
        terms=[term8_a],
    )

    codelist10 = Codelist(
        uid=f"{effective_date}_C10",
        concept_id="C10",
        name="Codelist C10",
        submission_value="SM C10",
        preferred_term="PT C10",
        definition="Definition C10",
        extensible=True,
        synonyms=None,
        terms=[term8_b],
    )

    codelist11 = Codelist(
        uid=f"{effective_date}_C11",
        concept_id="C11",
        name="Codelist C11",
        submission_value="SM C11",
        preferred_term="PT C11",
        definition="Definition C11",
        extensible=True,
        synonyms=None,
        terms=[term8_c],
    )

    package6 = Package(
        uid=f"{effective_date}_CAT6 CT",
        catalogue_name="CAT6 CT",
        registration_status="Final",
        name="CAT6 CT 2020-01-01",
        label="Cat6 Controlled Terminology Package 1 Effective 2020-01-01",
        description="The codelists C09, C10 and C11 have the same term with different submission values -> log inconsistency",
        source="Cat6 source",
        href="/mdr/ct/packages/cat6-2020-01-01",
        terms=[term8_b, term8_a, term8_c],
        codelists=[codelist9, codelist10, codelist11],
        discontinued_codelists=[],
    )

    codelist12 = Codelist(
        uid=f"{effective_date}_C12",
        concept_id="C12",
        name="Codelist C12",
        submission_value="SM C12",
        preferred_term="PT C12",
        definition="Definition C12 - same name-T08 submission value as codelist C09 from 'Cat6 CT 2020-01-01'",
        extensible=True,
        synonyms=None,
        terms=[term8_a],
    )

    package7 = Package(
        uid=f"{effective_date}_CAT7 CT",
        catalogue_name="CAT7 CT",
        registration_status="Final",
        name="CAT7 CT 2020-01-01",
        label="Cat7 Controlled Terminology Package 1 Effective 2020-01-01",
        description="The codelist C12 contains the same term as in codelist C09 from 'Cat6 CT 2020-01-01'",
        source="Cat7 source",
        href="/mdr/ct/packages/cat7-2020-01-01",
        terms=[term8_a],
        codelists=[codelist12],
        discontinued_codelists=[],
    )

    import1 = Import(
        effective_date=effective_date,
        author_id=author_id,
        packages=[package1, package2, package3, package4, package5, package6, package7],
        discontinued_codelists=[],
        log_entries=[warning1, warning4, warning2, info1, info2],
    )

    return [import1]
