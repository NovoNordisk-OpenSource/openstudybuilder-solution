import itertools
import unittest

from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_codelist_attributes_repository import (
    CTCodelistAttributesRepository,
)
from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_codelist_name_repository import (
    CTCodelistNameRepository,
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


class TestCTCodelistRepository(unittest.TestCase):
    TEST_DB_NAME = "cttests.codelists.repo"

    @classmethod
    def setUpClass(cls) -> None:
        cls.db = inject_and_clear_db(cls.TEST_DB_NAME)
        cls.db.cypher_query("""
        CREATE(:Library{name:"CDISC", is_editable:true})
        CREATE(:Library{name:"Sponsor1", is_editable:true})
        CREATE(sdtm_ct:CTCatalogue{name:"SDTM CT"})-[:CONTAINS_PACKAGE]->(:CTPackage{uid: "SDTM_PACKAGE_1",name:"SDTM_PACKAGE_1"})
        MERGE(sdtm_ct)-[:CONTAINS_PACKAGE]->(:CTPackage{uid: "SDTM_PACKAGE_2", name:"SDTM_PACKAGE_2"})
        CREATE(cdash_ct:CTCatalogue{name:"CDASH CT"})-[:CONTAINS_PACKAGE]->(:CTPackage{uid: "CDASH_PACKAGE_1",name:"CDASH_PACKAGE_1"})
        MERGE(cdash_ct)-[:CONTAINS_PACKAGE]->(:CTPackage{uid: "CDASH_PACKAGE_2", name:"CDASH_PACKAGE_2"})
        """)
        cls.codelist_attributes_repo = CTCodelistAttributesRepository()
        cls.codelist_names_repo = CTCodelistNameRepository()

    @classmethod
    def tear_down_class(cls) -> None:
        cls.codelist_attributes_repo.close()
        cls.codelist_names_repo.close()

    def test__find_all__with_possible_filters_applied__returns_filtered_codelists(self):
        # given
        available_libraries = ["CDISC", "Sponsor1"]
        available_catalogues = ["SDTM CT", "CDASH CT"]
        available_packages = {
            "SDTM CT": ["SDTM_PACKAGE_1", "SDTM_PACKAGE_2"],
            "CDASH CT": ["CDASH_PACKAGE_1", "CDASH_PACKAGE_2"],
        }
        codelist_uid_to_package_name = {}
        for library in available_libraries:
            for catalogue in available_catalogues:
                for package_catalogue, packages in available_packages.items():
                    for _ in range(2):
                        codelist_attributes = create_random_ct_codelist_attributes_ar(
                            library=library, is_editable=True, catalogue=catalogue
                        )
                        codelist_attributes.approve(author_id=current_function_name())
                        self.codelist_attributes_repo.save(codelist_attributes)
                        codelist_names = create_random_ct_codelist_name_ar(
                            generate_uid_callback=lambda x=codelist_attributes.uid: x,
                            library=library,
                            is_editable=True,
                            catalogue=catalogue,
                        )
                        codelist_names.approve(author_id=current_function_name())
                        self.codelist_names_repo.save(codelist_names)
                        if catalogue == package_catalogue:
                            codelist_uid_to_package_name[codelist_attributes.uid] = (
                                packages
                            )
                            for package in packages:
                                self.db.cypher_query(
                                    """
                                MATCH(package:CTPackage {name: $package_name})
                                MATCH(codelist_attributes_value:CTCodelistAttributesValue {name: $codelist_name})
                                MERGE(package)-[:CONTAINS_CODELIST]->(:CTPackageCodelist)-
                                [:CONTAINS_ATTRIBUTES]->(codelist_attributes_value)
                                """,
                                    {
                                        "package_name": package,
                                        "codelist_name": codelist_attributes.name,
                                    },
                                )

        available_catalogues.append(None)
        available_libraries.append(None)
        available_packages = [
            value for key, values in available_packages.items() for value in values
        ]
        available_packages.append(None)
        # Initializes all possible combinations of filtering parameters with possibility of assigning None to them
        # The following mappings describes the possible optional filter parameters:
        # * catalogue.name = filter_tuple[0]
        # * library.name = filter_tuple[1]
        # * package.name = filter_tuple[2]
        filter_tuples = itertools.product(
            available_catalogues, available_libraries, available_packages
        )
        for filter_tuple in filter_tuples:
            with self.subTest(filter_tuple):
                all_codelists_attributes_in_db = self.codelist_attributes_repo.find_all(
                    catalogue_name=filter_tuple[0],
                    library_name=filter_tuple[1],
                    package=filter_tuple[2],
                ).items

                all_codelists_names_in_db = self.codelist_names_repo.find_all(
                    catalogue_name=filter_tuple[0],
                    library_name=filter_tuple[1],
                    package=filter_tuple[2],
                ).items

                # Check if result lists contains the same length of results
                self.assertEqual(
                    len(all_codelists_attributes_in_db), len(all_codelists_names_in_db)
                )

                # check if Codelists are properly filtered
                for codelist_attributes, codelist_names in zip(
                    all_codelists_attributes_in_db, all_codelists_names_in_db
                ):
                    if filter_tuple[0] is not None:
                        self.assertEqual(
                            codelist_attributes.ct_codelist_vo.catalogue_names[0],
                            filter_tuple[0],
                        )
                        self.assertEqual(
                            codelist_names.ct_codelist_vo.catalogue_names[0],
                            filter_tuple[0],
                        )
                    if filter_tuple[1] is not None:
                        self.assertEqual(
                            codelist_attributes.library.name, filter_tuple[1]
                        )
                        self.assertEqual(codelist_names.library.name, filter_tuple[1])
                    if filter_tuple[2] is not None:
                        self.assertIn(
                            filter_tuple[2],
                            codelist_uid_to_package_name[codelist_attributes.uid],
                        )
                        self.assertIn(
                            filter_tuple[2],
                            codelist_uid_to_package_name[codelist_attributes.uid],
                        )

                # Check if result lists contains unique terms
                attributes_uids = [
                    attributes.uid for attributes in all_codelists_attributes_in_db
                ]
                names_uids = [names.uid for names in all_codelists_names_in_db]
                self.assertEqual(
                    len(attributes_uids),
                    len(set(attributes_uids)),
                    "CTCodelistAttributes are duplicated in the repository response",
                )
                self.assertEqual(
                    len(names_uids),
                    len(set(names_uids)),
                    "CTCodelistName are duplicated in the repository response",
                )
