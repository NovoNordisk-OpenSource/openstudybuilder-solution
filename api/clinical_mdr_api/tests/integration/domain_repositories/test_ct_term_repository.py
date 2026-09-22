import itertools
import unittest
from typing import Any

from neomodel import db

from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_codelist_attributes_repository import (
    CTCodelistAttributesRepository,
)
from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_codelist_name_repository import (
    CTCodelistNameRepository,
)
from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_term_aggregated_repository import (
    CTTermAggregatedRepository,
)
from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_term_attributes_repository import (
    CTTermAttributesRepository,
)
from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_term_name_repository import (
    CTTermNameRepository,
)
from clinical_mdr_api.tests.integration.domain_repositories._utils import (
    current_function_name,
)
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.unit.domain.controlled_terminology_aggregates.test_ct_codelist_attributes import (
    create_random_ct_codelist_attributes_ar,
)
from clinical_mdr_api.tests.unit.domain.controlled_terminology_aggregates.test_ct_codelist_name import (
    create_random_ct_codelist_name_ar,
)
from clinical_mdr_api.tests.unit.domain.controlled_terminology_aggregates.test_ct_term_attributes import (
    create_random_ct_term_attributes_ar,
)
from clinical_mdr_api.tests.unit.domain.controlled_terminology_aggregates.test_ct_term_names import (
    create_random_ct_term_name_ar,
)
from clinical_mdr_api.tests.unit.domain.utils import AUTHOR_ID


class TestCTTermRepository(unittest.TestCase):
    TEST_DB_NAME = "cttests.terms.repo"

    @classmethod
    def setUpClass(cls) -> None:
        inject_and_clear_db(cls.TEST_DB_NAME)
        db.cypher_query("""
        CREATE(:Library{name:"CDISC", is_editable:true})
        CREATE(:Library{name:"Sponsor", is_editable:true})
        CREATE(sdtm_ct:CTCatalogue{name:"SDTM CT"})-[:CONTAINS_PACKAGE]->(:CTPackage{uid: "SDTM_PACKAGE_1",name:"SDTM_PACKAGE_1"})
        MERGE(sdtm_ct)-[:CONTAINS_PACKAGE]->(:CTPackage{uid: "SDTM_PACKAGE_2", name:"SDTM_PACKAGE_2"})
        CREATE(cdash_ct:CTCatalogue{name:"CDASH CT"})-[:CONTAINS_PACKAGE]->(:CTPackage{uid: "CDASH_PACKAGE_1",name:"CDASH_PACKAGE_1"})
        MERGE(cdash_ct)-[:CONTAINS_PACKAGE]->(:CTPackage{uid: "CDASH_PACKAGE_2", name:"CDASH_PACKAGE_2"})
        """)
        cls.term_aggregated_repo = CTTermAggregatedRepository()
        cls.term_attributes_repo = CTTermAttributesRepository()
        cls.term_names_repo = CTTermNameRepository()
        cls.codelist_attributes_repo = CTCodelistAttributesRepository()
        cls.codelist_names_repo = CTCodelistNameRepository()

    @classmethod
    def tear_down_class(cls) -> None:
        cls.term_aggregated_repo.close()
        cls.term_attributes_repo.close()
        cls.term_names_repo.close()
        cls.codelist_attributes_repo.close()
        cls.codelist_names_repo.close()

    def test__find_all__with_possible_filters_applied__returns_filtered_codelists(self):
        # given
        available_codelists = []
        available_codelist_names = []
        codelist_uid_to_name_dict = {}
        available_catalogues = ["SDTM CT", "CDASH CT"]
        available_libraries = ["CDISC", "Sponsor"]
        available_packages = {
            "SDTM CT": ["SDTM_PACKAGE_1", "SDTM_PACKAGE_2"],
            "CDASH CT": ["CDASH_PACKAGE_1", "CDASH_PACKAGE_2"],
        }
        term_uid_to_package_name = {}
        all_terms_for_package: dict[Any, Any] = {}
        all_terms_for_library: dict[Any, Any] = {}
        all_terms_for_codelist: dict[Any, Any] = {}
        all_terms_for_codelist_name: dict[Any, Any] = {}

        for cl_library in available_libraries:
            for catalogue in available_catalogues:
                for _ in range(2):
                    with db.transaction:
                        codelist_attributes = create_random_ct_codelist_attributes_ar(
                            library=cl_library, is_editable=True, catalogue=catalogue
                        )

                        codelist_attributes.approve(author_id=current_function_name())
                        self.codelist_attributes_repo.save(codelist_attributes)
                        codelist_names = create_random_ct_codelist_name_ar(
                            generate_uid_callback=lambda x=codelist_attributes.uid: x,
                            library=cl_library,
                            is_editable=True,
                            catalogue=catalogue,
                        )
                        codelist_names.approve(author_id=current_function_name())
                        self.codelist_names_repo.save(codelist_names)

                    available_codelists.append(codelist_attributes.uid)
                    available_codelist_names.append(codelist_names.name)
                    codelist_uid_to_name_dict[codelist_attributes.uid] = (
                        codelist_names.name
                    )
                    all_terms_for_codelist[codelist_attributes.uid] = []
                    all_terms_for_codelist_name[codelist_names.name] = []

                    # for codelist in available_codelists:
                    term_order = 1
                    for term_library in available_libraries:
                        for package_catalogue, packages in available_packages.items():
                            for _ in range(1):
                                term_attributes = create_random_ct_term_attributes_ar(
                                    library=term_library,
                                    is_editable=True,
                                )
                                term_attributes.approve(
                                    author_id=current_function_name()
                                )
                                self.term_attributes_repo.save(term_attributes)
                                term_names = create_random_ct_term_name_ar(
                                    generate_uid_callback=lambda x=term_attributes.uid: x,
                                    library=term_library,
                                    is_editable=True,
                                )
                                term_names.approve(author_id=current_function_name())
                                self.term_names_repo.save(term_names)
                                if catalogue == package_catalogue:
                                    term_uid_to_package_name[term_attributes.uid] = (
                                        packages
                                    )
                                    for package in packages:
                                        db.cypher_query(
                                            """
                                        MATCH(package:CTPackage {name: $package_name})
                                        MATCH(term_attributes_value:CTTermAttributesValue {preferred_term: $term_name})
                                        MERGE(package)-[:CONTAINS_CODELIST]->(package_codelist:CTPackageCodelist)-[:CONTAINS_TERM]->
                                        (package_term:CTPackageTerm)-[:CONTAINS_ATTRIBUTES]->(term_attributes_value)
                                        """,
                                            {
                                                "package_name": package,
                                                "term_name": term_attributes.name,
                                            },
                                        )
                                        if all_terms_for_package.get(package) is None:
                                            all_terms_for_package[package] = [
                                                term_attributes.uid
                                            ]
                                        elif (
                                            term_attributes.uid
                                            not in all_terms_for_package[package]
                                        ):
                                            all_terms_for_package[package].append(
                                                term_attributes.uid
                                            )
                                res_data, attributes = db.cypher_query(
                                    """
                                        MATCH(:CTCatalogue {name: $catalogue})-[:HAS_CODELIST]->
                                        (codelist_root:CTCodelistRoot)<-[:CONTAINS_CODELIST]-(:Library{name:$library})
                                        MATCH (codelist_root)-[:HAS_NAME_ROOT]->(codelist_ver_root)-[:LATEST]->(codelist_ver_value)
                                        where codelist_root.uid <> $codelist_uid
                                        RETURN codelist_root.uid AS codelist_uid, codelist_ver_value.name as codelist_name
                                        """,
                                    {
                                        "catalogue": catalogue,
                                        "library": cl_library,
                                        "codelist_uid": codelist_attributes.uid,
                                    },
                                )
                                if len(res_data) > 0:
                                    codelist_uid = res_data[0][
                                        attributes.index("codelist_uid")
                                    ]
                                    codelist_name = res_data[0][
                                        attributes.index("codelist_name")
                                    ]
                                    self.codelist_attributes_repo.add_term(
                                        codelist_uid=codelist_uid,
                                        term_uid=term_attributes.uid,
                                        author_id=AUTHOR_ID,
                                        order=term_order,
                                        submission_value=term_attributes.name,
                                    )
                                    term_order += 1
                                    all_terms_for_codelist[codelist_uid].append(
                                        term_attributes.uid
                                    )
                                    all_terms_for_codelist_name[codelist_name].append(
                                        term_attributes.uid
                                    )

                                if all_terms_for_library.get(term_library) is None:
                                    all_terms_for_library[term_library] = [
                                        term_attributes.uid
                                    ]
                                elif (
                                    term_attributes.uid
                                    not in all_terms_for_library[term_library]
                                ):
                                    all_terms_for_library[term_library].append(
                                        term_attributes.uid
                                    )

        available_codelists.append(None)
        available_codelist_names.append(None)
        available_libraries.append(None)
        available_packages = [
            value for key, values in available_packages.items() for value in values
        ]
        available_packages.append(None)

        # Initializes all possible combinations of filtering parameters with possibility of assigning None to them
        # The following mappings describes the possible optional filter parameters:
        # * codelist.uid = cl_uid
        # * codelist.name = cl_name
        # * library = library
        # * package.name = package
        filter_tuples = itertools.product(
            available_codelists,
            available_codelist_names,
            available_libraries,
            available_packages,
        )
        for cl_uid, cl_name, library, package in filter_tuples:
            with self.subTest(f"{cl_uid}, {cl_name}, {library}, {package}"):
                all_term_in_db_aggregated_res = (
                    self.term_aggregated_repo.find_all_aggregated_result(
                        codelist_uid=cl_uid,
                        codelist_name=cl_name,
                        library=library,
                        package=package,
                    )[0]
                )
                all_filters_results = []
                # check if Terms are properly filtered
                for (
                    term_names,
                    term_attributes,
                    codelists,
                ) in all_term_in_db_aggregated_res:
                    if cl_uid is not None:
                        self.assertEqual(
                            codelists.codelists[0].codelist_uid,
                            cl_uid,
                        )
                        self.assertEqual(
                            codelists.codelists[0].codelist_uid,
                            cl_uid,
                        )
                        all_filters_results.append(set(all_terms_for_codelist[cl_uid]))
                    if cl_name is not None:
                        self.assertEqual(
                            codelist_uid_to_name_dict[
                                codelists.codelists[0].codelist_uid
                            ],
                            cl_name,
                        )
                        self.assertEqual(
                            codelist_uid_to_name_dict[
                                codelists.codelists[0].codelist_uid
                            ],
                            cl_name,
                        )
                        all_filters_results.append(
                            set(all_terms_for_codelist_name[cl_name])
                        )
                    if library is not None:
                        self.assertEqual(term_attributes.library.name, library)
                        self.assertEqual(term_names.library.name, library)
                        all_filters_results.append(set(all_terms_for_library[library]))
                    if package is not None:
                        self.assertIn(
                            package,
                            term_uid_to_package_name[term_attributes.uid],
                        )
                        self.assertIn(
                            package,
                            term_uid_to_package_name[term_attributes.uid],
                        )
                        all_filters_results.append(set(all_terms_for_package[package]))

                predicted_result = set()
                if len(all_filters_results) > 0:
                    predicted_result = set.intersection(*all_filters_results)
                # query without filters
                elif (
                    len(all_term_in_db_aggregated_res) > 0
                    and len(all_filters_results) == 0
                ):
                    predicted_result = set.union(
                        {
                            item
                            for sublist in all_terms_for_codelist.values()
                            for item in sublist
                        },
                        {
                            item
                            for sublist in all_terms_for_codelist_name.values()
                            for item in sublist
                        },
                        {
                            item
                            for sublist in all_terms_for_library.values()
                            for item in sublist
                        },
                        {
                            item
                            for sublist in all_terms_for_package.values()
                            for item in sublist
                        },
                    )

                # Check that we got the expected terms
                assert predicted_result == set(
                    name.uid for name, _, _ in all_term_in_db_aggregated_res
                )

                # Check if result lists contains unique terms
                # the tuples of (term_uid, codelist_uid) are compared, as we allow multiple same term_uid unless if they
                # come from different codelists
                def get_cl_uid(codelists):
                    if len(codelists.codelists) > 0:
                        return codelists.codelists[0].codelist_uid
                    return None

                attributes_uids = [
                    (attributes.uid, get_cl_uid(codelists))
                    for _, attributes, codelists in all_term_in_db_aggregated_res
                ]
                self.assertEqual(
                    len(attributes_uids),
                    len(set(attributes_uids)),
                    "CTTermsAttributes are duplicated in the repository response",
                )
                names_uids = [
                    (names.uid, get_cl_uid(codelists))
                    for names, _, codelists in all_term_in_db_aggregated_res
                ]
                self.assertEqual(
                    len(names_uids),
                    len(set(names_uids)),
                    "CTTermNames are duplicated in the repository response",
                )
