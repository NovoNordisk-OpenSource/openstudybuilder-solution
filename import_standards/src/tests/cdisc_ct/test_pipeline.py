# import datetime
# from os import environ

# from neo4j import GraphDatabase

# # from mdr_standards_import.cdisc_ct.load_ct_preprocessing import run_preprocessing_step, Codelist, Term
# from mdr_standards_import.cdisc_ct.utils import are_lists_equal

# cdisc_import_neo4j_driver = GraphDatabase.driver("neo4j://{}:{}".format(
#     environ.get("NEO4J_CDISC_IMPORT_HOST"),
#     environ.get("NEO4J_CDISC_IMPORT_BOLT_PORT")
# ), auth=(
#     environ.get("NEO4J_CDISC_IMPORT_AUTH_USER"),
#     environ.get("NEO4J_CDISC_IMPORT_AUTH_PASSWORD")
# ))

# mdr_neo4j_driver = GraphDatabase.driver("neo4j://{}:{}".format(
#     environ.get("NEO4J_MDR_HOST"),
#     environ.get("NEO4J_MDR_BOLT_PORT")
# ), auth=(
#     environ.get("NEO4J_MDR_AUTH_USER"),
#     environ.get("NEO4J_MDR_AUTH_PASSWORD")
# ))

# cdisc_db_name = "import-test"
# mdr_db_name = "mdr-test"


# def setup_module():
#     print("\n *** setup_module ***")
#     with cdisc_import_neo4j_driver.session(database="system") as session:
#         session.run("CREATE DATABASE $database IF NOT EXISTS", database=cdisc_db_name)
#     with mdr_neo4j_driver.session(database="system") as session:
#         session.run("CREATE DATABASE $database IF NOT EXISTS", database=mdr_db_name)


# def teardown_module():
#     print("\n *** teardown_module ***")


# class Package:
#     def __init__(self, uid=None, catalogue_name=None, registration_status=None, name=None, label=None, description=None,
#                  source=None, href=None, terms=None, codelists=None, discontinued_codelists=None):
#         self.uid = uid
#         self.catalogue_name = catalogue_name
#         self.registration_status = registration_status
#         self.name = name
#         self.label = label
#         self.description = description
#         self.source = source
#         self.href = href

#         self.terms = terms
#         self.codelists = codelists
#         self.discontinued_codelists = discontinued_codelists

#     @staticmethod
#     def from_node_record(node_record):
#         package = Package()
#         if node_record:
#             package.uid = node_record.get('uid', None)
#             package.catalogue_name = node_record.get('catalogue_name', None)
#             package.registration_status = node_record.get('registration_status', None)
#             package.name = node_record.get('name', None)
#             package.label = node_record.get('label', None)
#             package.description = node_record.get('description', None)
#             package.source = node_record.get('source', None)
#             package.href = node_record.get('href', None)

#         return package


# class Import:
#     def __init__(self, effective_date=None, author_id=None, packages=None, discontinued_codelists=None,
#                  log_entries=None):
#         self.effective_date = effective_date
#         self.author_id = author_id
#         self.import_date = None
#         self.packages = packages
#         self.discontinued_codelists = discontinued_codelists
#         self.log_entries = log_entries

#     @staticmethod
#     def from_node_record(node_record):
#         import_object = Import()
#         if node_record:
#             import_object.effective_date = node_record.get('effective_date', None)
#             import_object.import_date = node_record.get('import_date', None)
#             import_object.author_id = node_record.get('author_id', None)

#             import_object.packages = node_record.get('packages', None)

#         return import_object


# class Log:
#     def __init__(self, level="Info", tagline=None, message=None, affected_uid=None):
#         self.level = level
#         self.tagline = tagline
#         self.message = message
#         # the uid property of the affected Package, Codelist or Term
#         self.affected_uid = affected_uid

#     @staticmethod
#     def from_node_record(node_record):
#         log = Log()
#         if node_record:
#             print(node_record)
#             labels = node_record.labels
#             assert len(labels) == 2
#             assert "Log" in labels

#             if "Warning" in labels:
#                 log.level = "Warning"
#             elif "Info" in labels:
#                 log.level = "Info"
#             else:
#                 log.level = "Unknown"

#             log.tagline = node_record.get('tagline', None)
#             log.message = node_record.get('message', None)
#         return log


# # class TestCDISCImportDb:

# #     @staticmethod
# #     def setup_method(test_method):
# #         print("\n*** setup_method ***")
# #         with cdisc_import_neo4j_driver.session(database=cdisc_db_name) as session:
# #             session.run("MATCH (n) DETACH DELETE n")
# #         with mdr_neo4j_driver.session(database=mdr_db_name) as session:
# #             session.run("MATCH (n) DETACH DELETE n")

# #     @staticmethod
# #     def teardown_method(test_method):
# #         print("\n*** teardown_method ***")

# #     def test__cdisc_import_case1(self):
# #         # given
# #         effective_date = "2020-01-01"
# #         data_dir = "./mdr_standards_import/tests/cdisc_ct/json_data/case1"
# #         author_id = "TST"

# #         # when
# #         run_preprocessing_step(effective_date, data_dir, cdisc_import_neo4j_driver, cdisc_db_name, mdr_neo4j_driver,
# #                                mdr_db_name, author_id)

# #         # then
# #         TestCDISCImportDb.assert_number_of_nodes(expected_num_imports=1, expected_num_packages=1,
# #                                                  expected_num_codelists=1, expected_num_terms=1,
# #                                                  expected_num_submission_values=1, expected_num_info_messages=0,
# #                                                  expected_num_warning_messages=0)
# #         from mdr_standards_import.tests.cdisc_ct.expected_preprocessing_data.case1 import get_expected_imports
# #         TestCDISCImportDb.assert_imports(get_expected_imports(effective_date, author_id))

# #     def test__cdisc_import_case2(self):
# #         # given
# #         effective_date = "2020-01-01"
# #         data_dir = "./mdr_standards_import/tests/cdisc_ct/json_data/case2"
# #         author_id = "TST"

# #         # when
# #         run_preprocessing_step(effective_date, data_dir, cdisc_import_neo4j_driver, cdisc_db_name, mdr_neo4j_driver,
# #                                mdr_db_name, author_id)

# #         # then
# #         TestCDISCImportDb.assert_number_of_nodes(expected_num_imports=1, expected_num_packages=1,
# #                                                  expected_num_codelists=4, expected_num_terms=2,
# #                                                  expected_num_submission_values=4, expected_num_info_messages=0,
# #                                                  expected_num_warning_messages=0)
# #         from mdr_standards_import.tests.cdisc_ct.expected_preprocessing_data.case2 import get_expected_imports
# #         TestCDISCImportDb.assert_imports(get_expected_imports(effective_date, author_id))

# #     def test__cdisc_import_case3(self):
# #         # given
# #         effective_date = "2020-01-01"
# #         data_dir = "./mdr_standards_import/tests/cdisc_ct/json_data/case3"
# #         author_id = "TST"

# #         # when
# #         run_preprocessing_step(effective_date, data_dir, cdisc_import_neo4j_driver, cdisc_db_name, mdr_neo4j_driver,
# #                                mdr_db_name, author_id)

# #         # then
# #         TestCDISCImportDb.assert_number_of_nodes(expected_num_imports=1, expected_num_packages=1,
# #                                                  expected_num_codelists=1, expected_num_terms=1,
# #                                                  expected_num_submission_values=1, expected_num_info_messages=1,
# #                                                  expected_num_warning_messages=0)
# #         from mdr_standards_import.tests.cdisc_ct.expected_preprocessing_data.case3 import get_expected_imports
# #         TestCDISCImportDb.assert_imports(get_expected_imports(effective_date, author_id))

# #     def test__cdisc_import_case4(self):
# #         # given
# #         effective_date = "2020-01-01"
# #         data_dir = "./mdr_standards_import/tests/cdisc_ct/json_data/case4"
# #         author_id = "TST"

# #         # when
# #         run_preprocessing_step(effective_date, data_dir, cdisc_import_neo4j_driver, cdisc_db_name, mdr_neo4j_driver,
# #                                mdr_db_name, author_id)

# #         # then
# #         TestCDISCImportDb.assert_number_of_nodes(expected_num_imports=1, expected_num_packages=1,
# #                                                  expected_num_codelists=3, expected_num_terms=1,
# #                                                  expected_num_submission_values=1, expected_num_info_messages=2,
# #                                                  expected_num_warning_messages=0)
# #         from mdr_standards_import.tests.cdisc_ct.expected_preprocessing_data.case4 import get_expected_imports
# #         TestCDISCImportDb.assert_imports(get_expected_imports(effective_date, author_id))

# #     def test__cdisc_import_case5(self):
# #         # given
# #         effective_date = "2020-01-01"
# #         data_dir = "./mdr_standards_import/tests/cdisc_ct/json_data/case5"
# #         author_id = "TST"

# #         # when
# #         run_preprocessing_step(effective_date, data_dir, cdisc_import_neo4j_driver, cdisc_db_name, mdr_neo4j_driver,
# #                                mdr_db_name, author_id)

# #         # then
# #         TestCDISCImportDb.assert_number_of_nodes(expected_num_imports=1, expected_num_packages=1,
# #                                                  expected_num_codelists=2, expected_num_terms=1,
# #                                                  expected_num_submission_values=2, expected_num_info_messages=0,
# #                                                  expected_num_warning_messages=0)
# #         from mdr_standards_import.tests.cdisc_ct.expected_preprocessing_data.case5 import get_expected_imports
# #         TestCDISCImportDb.assert_imports(get_expected_imports(effective_date, author_id))

# #     def test__cdisc_import_case6(self):
# #         # given
# #         effective_date = "2020-01-01"
# #         data_dir = "./mdr_standards_import/tests/cdisc_ct/json_data/case6"
# #         author_id = "TST"

# #         # when
# #         run_preprocessing_step(effective_date, data_dir, cdisc_import_neo4j_driver, cdisc_db_name, mdr_neo4j_driver,
# #                                mdr_db_name, author_id)

# #         # then
# #         TestCDISCImportDb.assert_number_of_nodes(expected_num_imports=1, expected_num_packages=1,
# #                                                  expected_num_codelists=2, expected_num_terms=1,
# #                                                  expected_num_submission_values=2, expected_num_info_messages=0,
# #                                                  expected_num_warning_messages=0)
# #         from mdr_standards_import.tests.cdisc_ct.expected_preprocessing_data.case6 import get_expected_imports
# #         TestCDISCImportDb.assert_imports(get_expected_imports(effective_date, author_id))

# #     def test__cdisc_import_case7(self):
# #         # given
# #         effective_date = "2020-01-01"
# #         data_dir = "./mdr_standards_import/tests/cdisc_ct/json_data/case7"
# #         author_id = "TST"

# #         # when
# #         run_preprocessing_step(effective_date, data_dir, cdisc_import_neo4j_driver, cdisc_db_name, mdr_neo4j_driver,
# #                                mdr_db_name, author_id)

# #         # then
# #         TestCDISCImportDb.assert_number_of_nodes(expected_num_imports=1, expected_num_packages=1,
# #                                                  expected_num_codelists=6, expected_num_terms=4,
# #                                                  expected_num_submission_values=8, expected_num_info_messages=0,
# #                                                  expected_num_warning_messages=0)
# #         from mdr_standards_import.tests.cdisc_ct.expected_preprocessing_data.case7 import get_expected_imports
# #         TestCDISCImportDb.assert_imports(get_expected_imports(effective_date, author_id))

# #     def test__cdisc_import_case8(self):
# #         # given
# #         effective_date = "2020-01-01"
# #         data_dir = "./mdr_standards_import/tests/cdisc_ct/json_data/case8"
# #         author_id = "TST"

# #         # when
# #         run_preprocessing_step(effective_date, data_dir, cdisc_import_neo4j_driver, cdisc_db_name, mdr_neo4j_driver,
# #                                mdr_db_name, author_id)

# #         # then
# #         TestCDISCImportDb.assert_number_of_nodes(expected_num_imports=1, expected_num_packages=1,
# #                                                  expected_num_codelists=4, expected_num_terms=4,
# #                                                  expected_num_submission_values=3, expected_num_info_messages=0,
# #                                                  expected_num_warning_messages=1)
# #         from mdr_standards_import.tests.cdisc_ct.expected_preprocessing_data.case8 import get_expected_imports
# #         TestCDISCImportDb.assert_imports(get_expected_imports(effective_date, author_id))

# #     def test__cdisc_import_case9(self):
# #         # given
# #         effective_date = "2020-01-01"
# #         data_dir = "./mdr_standards_import/tests/cdisc_ct/json_data/case9"
# #         author_id = "TST"

# #         # when
# #         run_preprocessing_step(effective_date, data_dir, cdisc_import_neo4j_driver, cdisc_db_name, mdr_neo4j_driver,
# #                                mdr_db_name, author_id)

# #         # then
# #         TestCDISCImportDb.assert_number_of_nodes(expected_num_imports=1, expected_num_packages=1,
# #                                                  expected_num_codelists=2, expected_num_terms=2,
# #                                                  expected_num_submission_values=2, expected_num_info_messages=0,
# #                                                  expected_num_warning_messages=0)
# #         from mdr_standards_import.tests.cdisc_ct.expected_preprocessing_data.case9 import get_expected_imports
# #         TestCDISCImportDb.assert_imports(get_expected_imports(effective_date, author_id))

# #     def test__cdisc_import_case10(self):
# #         # given
# #         effective_date = "2020-01-01"
# #         data_dir = "./mdr_standards_import/tests/cdisc_ct/json_data/case10"
# #         author_id = "TST"

# #         # when
# #         run_preprocessing_step(effective_date, data_dir, cdisc_import_neo4j_driver, cdisc_db_name, mdr_neo4j_driver,
# #                      mdr_db_name, author_id)

# #         # then
# #         TestCDISCImportDb.assert_number_of_nodes(expected_num_imports=1, expected_num_packages=7,
# #                                                  expected_num_codelists=12, expected_num_terms=11,
# #                                                  expected_num_submission_values=12, expected_num_info_messages=2,
# #                                                  expected_num_warning_messages=3)
# #         from mdr_standards_import.tests.cdisc_ct.expected_preprocessing_data.case10 import get_expected_imports
# #         TestCDISCImportDb.assert_imports(get_expected_imports(effective_date, author_id))

# #     def test__cdisc_import_case10_2(self):
# #         # given
# #         effective_date = "2020-02-01"
# #         data_dir = "./mdr_standards_import/tests/cdisc_ct/json_data/case10"
# #         author_id = "TST"

# #         # when
# #         run_preprocessing_step("2020-01-01", data_dir, cdisc_import_neo4j_driver, cdisc_db_name, mdr_neo4j_driver,
# #                      mdr_db_name, author_id)
# #         run_preprocessing_step(effective_date, data_dir, cdisc_import_neo4j_driver, cdisc_db_name, mdr_neo4j_driver,
# #                      mdr_db_name, author_id)

# #         # then
# #         number_of_discontinued_codelists = 3
# #         TestCDISCImportDb.assert_number_of_nodes(expected_num_imports=2, expected_num_packages=7 + 4,
# #                                                  expected_num_codelists=12 + 5 + number_of_discontinued_codelists,
# #                                                  expected_num_terms=11 + 5,
# #                                                  expected_num_submission_values=12 + 6, expected_num_info_messages=2,
# #                                                  expected_num_warning_messages=5)
# #         from mdr_standards_import.tests.cdisc_ct.expected_preprocessing_data.case10 import get_expected_imports
# #         # TestCDISCImportDb.assert_imports(get_expected_imports(effective_date, author_id))

# #     @staticmethod
# #     def assert_number_of_nodes(expected_num_imports, expected_num_packages, expected_num_codelists, expected_num_terms,
# #                                expected_num_submission_values,
# #                                expected_num_info_messages, expected_num_warning_messages):
# #         with cdisc_import_neo4j_driver.session(database=cdisc_db_name) as session:
# #             actual_result = session.run(
# #                 """
# #                 MATCH (import:Import) WITH count(import) AS num_imports
# #                 MATCH (package:Package) WITH num_imports, count(package) AS num_packages
# #                 MATCH (codelist:Codelist) WITH num_imports, num_packages, count(codelist) AS num_codelists
# #                 MATCH (term:Term) WITH num_imports, num_packages, num_codelists, count(term) AS num_terms
# #                 MATCH (submission_value:SubmissionValue)
# #                 WITH num_imports, num_packages, num_codelists, num_terms,
# #                     count(submission_value) AS num_submission_values
# #                 OPTIONAL MATCH (info:Info)
# #                 WITH num_imports, num_packages, num_codelists, num_terms, num_submission_values,
# #                     count(info) AS num_info_messages
# #                 OPTIONAL MATCH (warning:Warning)
# #                 WITH num_imports, num_packages, num_codelists, num_terms, num_submission_values, num_info_messages,
# #                     count(warning) AS num_warning_messages
# #                 RETURN num_imports, num_packages, num_codelists, num_terms, num_submission_values,
# #                     num_info_messages, num_warning_messages
# #                 """
# #             ).single()

# #             assert actual_result['num_imports'] == expected_num_imports
# #             assert actual_result['num_packages'] == expected_num_packages
# #             assert actual_result['num_codelists'] == expected_num_codelists
# #             assert actual_result['num_terms'] == expected_num_terms
# #             assert actual_result['num_submission_values'] == expected_num_submission_values
# #             assert actual_result['num_info_messages'] == expected_num_info_messages
# #             assert actual_result['num_warning_messages'] == expected_num_warning_messages

# #     @staticmethod
# #     def assert_imports(expected_imports):
# #         for expected_import in expected_imports:
# #             with cdisc_import_neo4j_driver.session(database=cdisc_db_name) as session:
# #                 result = session.run(
# #                     """
# #                     MATCH (import:Import{effective_date: date($effective_date)})
# #                     CALL {
# #                         WITH import
# #                         OPTIONAL MATCH (import)-[:INCLUDES]->(package)
# #                         WITH package
# #                         ORDER BY package.uid
# #                         RETURN collect(package) AS packages
# #                     }
# #                     CALL {
# #                         WITH import
# #                         OPTIONAL MATCH (import)-[:DISCONTINUES]->(codelist)
# #                         WITH codelist
# #                         ORDER BY codelist.uid
# #                         RETURN collect(codelist) AS discontinued_codelists
# #                     }
# #                     CALL {
# #                         WITH import
# #                         OPTIONAL MATCH (import)-[:HAS]->(log)--(affected_node)
# #                         WITH log, CASE WHEN 'Warning' IN labels(log) THEN 0 ELSE 1 END AS level_order
# #                         ORDER BY level_order, affected_node.uid, log.tagline, log.message
# #                         RETURN collect(log) AS log_entries
# #                     }
# #                     RETURN import, packages, discontinued_codelists, log_entries
# #                     """,
# #                     effective_date=expected_import.effective_date
# #                 ).single()

# #             TestCDISCImportDb.assert_import_properties(Import.from_node_record(result['import']), expected_import)

# #             print(f"assert (:Import{{effective_date: {expected_import.effective_date}}})-[:INCLUDES]->(package)")
# #             TestCDISCImportDb.assert_packages(result['packages'], expected_import.packages)

# #             print(f"assert (:Import{{effective_date: {expected_import.effective_date}}})-[:DISCONTINUES]->(codelist)")
# #             TestCDISCImportDb.assert_codelists(
# #                 result['discontinued_codelists'],
# #                 expected_import.discontinued_codelists,
# #                 True
# #             )

# #             print(f"assert (:Import{{effective_date: {expected_import.effective_date}}})-[:HAS]->(log)")
# #             TestCDISCImportDb.assert_log_entries(result['log_entries'], expected_import.log_entries)

# #     @staticmethod
# #     def assert_packages(actual_packages_result, expected_packages):
# #         assert len(actual_packages_result) == len(expected_packages)
# #         for package_index in range(0, len(actual_packages_result)):
# #             actual_package = Package.from_node_record(actual_packages_result[package_index])
# #             expected_package = expected_packages[package_index]

# #             TestCDISCImportDb.assert_package_properties(actual_package, expected_package)

# #             with cdisc_import_neo4j_driver.session(database=cdisc_db_name) as session:
# #                 result = session.run(
# #                     """
# #                     MATCH (package:Package{uid: $package_uid})
# #                     CALL {
# #                         WITH package
# #                         OPTIONAL MATCH (package)-[:CONTAINS]->(codelist)
# #                         WITH codelist
# #                         ORDER BY codelist.uid
# #                         RETURN collect(codelist) AS codelists
# #                     }
# #                     CALL {
# #                         WITH package
# #                         OPTIONAL MATCH (package)-[:CONTAINS_TERM]->(term)
# #                         WITH term
# #                         ORDER BY term.uid
# #                         RETURN collect(term) AS terms
# #                     }
# #                     CALL {
# #                         WITH package
# #                         OPTIONAL MATCH (package)-[:DISCONTINUES]->(codelist)
# #                         WITH codelist
# #                         ORDER BY codelist.uid
# #                         RETURN collect(codelist) AS discontinued_codelists
# #                     }
# #                     RETURN codelists, terms, discontinued_codelists
# #                     """
# #                     ,
# #                     package_uid=actual_package.uid
# #                 ).single()

# #             print(f"assert (:Package{{uid: {actual_package.uid}}})-[:CONTAINS]->(codelist)")
# #             TestCDISCImportDb.assert_codelists(result['codelists'], expected_package.codelists)

# #             print("assert (package)-[:CONTAINS_TERM]->(term)")
# #             TestCDISCImportDb.assert_terms(result['terms'], expected_package.terms)

# #             print("assert (package)-[:DISCONTINUES]->(codelist)")
# #             TestCDISCImportDb.assert_codelists(
# #                 result['discontinued_codelists'],
# #                 expected_package.discontinued_codelists
# #             )

# #     @staticmethod
# #     def assert_codelists(actual_codelists_result, expected_codelists, check_only_uid_and_concept_id=False):
# #         assert len(actual_codelists_result) == len(expected_codelists)
# #         for codelist_index in range(0, len(actual_codelists_result)):
# #             actual_codelist = Codelist.from_node_record(actual_codelists_result[codelist_index])
# #             expected_codelist = expected_codelists[codelist_index]

# #             TestCDISCImportDb.assert_codelist_properties(
# #                 actual_codelist,
# #                 expected_codelist,
# #                 check_only_uid_and_concept_id,
# #             )

# #             if not check_only_uid_and_concept_id:
# #                 with cdisc_import_neo4j_driver.session(database=cdisc_db_name) as session:
# #                     result = session.run(
# #                         """
# #                         MATCH (codelist:Codelist{uid: $codelist_uid})
# #                         OPTIONAL MATCH (codelist)-[:CONTAINS]->(term)
# #                         WITH term
# #                         ORDER BY term.uid
# #                         RETURN collect(term) AS terms
# #                         """
# #                         ,
# #                         codelist_uid=actual_codelist.uid
# #                     ).single()

# #                 print(f"assert (:Codelist {{uid: {actual_codelist.uid}}}))-[:CONTAINS]->(term)")
# #                 TestCDISCImportDb.assert_terms(result['terms'], expected_codelist.terms)

# #     @staticmethod
# #     def assert_terms(actual_term_result, expected_terms):
# #         assert len(actual_term_result) == len(expected_terms)
# #         for term_index in range(0, len(actual_term_result)):
# #             TestCDISCImportDb.assert_term_properties(
# #                 Term.from_node_record(actual_term_result[term_index]),
# #                 expected_terms[term_index]
# #             )

# #     @staticmethod
# #     def assert_log_entries(actual_log_entries_result, expected_log_entries):
# #         assert len(actual_log_entries_result) == len(expected_log_entries)
# #         for log_index in range(0, len(actual_log_entries_result)):
# #             actual_log_entry_result = actual_log_entries_result[log_index]
# #             expected_log_entry = expected_log_entries[log_index]

# #             TestCDISCImportDb.assert_log_entry_properties(
# #                 Log.from_node_record(actual_log_entry_result),
# #                 expected_log_entry
# #             )

# #             assert expected_log_entry.affected_uid

# #             with cdisc_import_neo4j_driver.session(database=cdisc_db_name) as session:
# #                 result = session.run(
# #                     """
# #                     MATCH (log:Log)-->(affected_node)
# #                     WHERE id(log) = $log_id
# #                     RETURN affected_node.uid AS affected_uid
# #                     """
# #                     ,
# #                     log_id=actual_log_entry_result.id
# #                 ).single()
# #                 assert result['affected_uid'] == expected_log_entry.affected_uid

# #     @staticmethod
# #     def assert_import_properties(actual_import, expected_import):
# #         assert actual_import.effective_date.iso_format() == expected_import.effective_date

# #         now = datetime.datetime.now()
# #         date = now.date()
# #         year = date.strftime("%Y")
# #         month = date.strftime("%-m")
# #         day = date.strftime("%-d")

# #         assert str(actual_import.import_date.year) == year
# #         assert str(actual_import.import_date.month) == month
# #         assert str(actual_import.import_date.day) == day

# #         assert actual_import.author_id == expected_import.author_id

# #     @staticmethod
# #     def assert_package_properties(actual_package, expected_package):
# #         assert actual_package.uid == expected_package.uid
# #         assert actual_package.catalogue_name == expected_package.catalogue_name
# #         assert actual_package.registration_status == expected_package.registration_status
# #         assert actual_package.name == expected_package.name
# #         assert actual_package.label == expected_package.label
# #         assert actual_package.description == expected_package.description
# #         assert actual_package.source == expected_package.source
# #         assert actual_package.href == expected_package.href

# #     @staticmethod
# #     def assert_term_properties(actual_term, expected_term):
# #         # print("assert_term_properties")
# #         # print(f"actual_term={vars(actual_term)}")
# #         # print(f"expected_term={vars(expected_term)}")

# #         assert actual_term.uid == expected_term.uid
# #         assert actual_term.concept_id == expected_term.concept_id
# #         assert actual_term.code_submission_value == expected_term.code_submission_value
# #         assert actual_term.name_submission_value == expected_term.name_submission_value
# #         assert actual_term.preferred_term == expected_term.preferred_term
# #         assert actual_term.definition == expected_term.definition
# #         assert are_lists_equal(actual_term.synonyms, expected_term.synonyms)

# #     @staticmethod
# #     def assert_codelist_properties(actual_codelist, expected_codelist, check_only_uid_and_concept_id=False):
# #         assert actual_codelist.uid == expected_codelist.uid
# #         assert actual_codelist.concept_id == expected_codelist.concept_id
# #         if check_only_uid_and_concept_id:
# #             return

# #         assert actual_codelist.name == expected_codelist.name
# #         assert actual_codelist.submission_value == expected_codelist.submission_value
# #         assert actual_codelist.preferred_term == expected_codelist.preferred_term
# #         assert actual_codelist.definition == expected_codelist.definition
# #         assert actual_codelist.extensible == expected_codelist.extensible
# #         assert are_lists_equal(actual_codelist.synonyms, expected_codelist.synonyms)

# #     @staticmethod
# #     def assert_log_entry_properties(actual_log_entry, expected_log_entry):
# #         assert actual_log_entry.level == expected_log_entry.level
# #         assert actual_log_entry.tagline == expected_log_entry.tagline
# #         # assert actual_log_entry.message == expected_log_entry.message
