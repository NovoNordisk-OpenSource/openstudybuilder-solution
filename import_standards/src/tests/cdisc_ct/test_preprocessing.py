# from mdr_standards_import.cdisc_ct.load_ct_preprocessing import *


# class Test1:
#     def test__are_codelist_attributes_consistent_empty_codelists(self):
#         # given
#         current_codelist = Codelist()
#         existing_codelist = Codelist()

#         # when, then
#         assert are_codelist_attributes_consistent(None, None, current_codelist, existing_codelist, True) is True

#     def test__are_codelist_attributes_consistent_true(self):
#         # given
#         current_codelist = Codelist()
#         current_codelist.uid = 'test-uid-1'
#         current_codelist.concept_id = 'test-concept-id-1'

#         existing_codelist = Codelist()
#         existing_codelist.uid = 'test-uid-2'
#         existing_codelist.concept_id = 'test-concept-id-2'

#         # when, then
#         assert are_codelist_attributes_consistent(None, None, current_codelist, existing_codelist, True) is True

#     def test__are_codelist_attributes_consistent_different_submission_value(self):
#         # given
#         current_codelist = Codelist()
#         current_codelist.uid = 'test-uid'
#         current_codelist.concept_id = 'test-concept-id'
#         current_codelist.submission_value = 'test-submission-value-1'

#         existing_codelist = Codelist()
#         existing_codelist.uid = 'test-uid'
#         existing_codelist.concept_id = 'test-concept-id'
#         existing_codelist.submission_value = 'test-submission-value-2'

#         # when, then
#         assert are_codelist_attributes_consistent(None, None, current_codelist, existing_codelist, True) is False

#     def test__are_codelist_attributes_consistent_different_name(self):
#         # given
#         current_codelist = Codelist()
#         current_codelist.uid = 'test-uid'
#         current_codelist.concept_id = 'test-concept-id'
#         current_codelist.submission_value = 'test-submission-value'
#         current_codelist.name = 'test-name-1'

#         existing_codelist = Codelist()
#         existing_codelist.uid = 'test-uid'
#         existing_codelist.concept_id = 'test-concept-id'
#         existing_codelist.submission_value = 'test-submission-value'
#         existing_codelist.name = 'test-name-2'

#         # when, then
#         assert are_codelist_attributes_consistent(None, None, current_codelist, existing_codelist, True) is False

#     def test__are_codelist_attributes_consistent_different_synonyms(self):
#         # given
#         current_codelist = Codelist()
#         current_codelist.uid = 'test-uid'
#         current_codelist.concept_id = 'test-concept-id'
#         current_codelist.submission_value = 'test-submission-value'
#         current_codelist.synonyms = ['s1', 's2']

#         existing_codelist = Codelist()
#         existing_codelist.uid = 'test-uid'
#         existing_codelist.concept_id = 'test-concept-id'
#         existing_codelist.submission_value = 'test-submission-value'
#         existing_codelist.synonyms = ['s1', 's2', '']

#         # when, then
#         assert are_codelist_attributes_consistent(None, None, current_codelist, existing_codelist, True) is False

#     def test__are_codelist_attributes_consistent_different_extensible(self):
#         # given
#         current_codelist = Codelist()
#         current_codelist.uid = 'test-uid'
#         current_codelist.concept_id = 'test-concept-id'
#         current_codelist.submission_value = 'test-submission-value'
#         current_codelist.synonyms = ['s1', 's2']
#         current_codelist.extensible = True

#         existing_codelist = Codelist()
#         existing_codelist.uid = 'test-uid'
#         existing_codelist.concept_id = 'test-concept-id'
#         existing_codelist.submission_value = 'test-submission-value'
#         existing_codelist.synonyms = ['s1', 's2']
#         existing_codelist.extensible = False

#         # when, then
#         assert are_codelist_attributes_consistent(None, None, current_codelist, existing_codelist, True) is False


# class Test2:
#     def test__are_term_attributes_consistent_empty_codelists(self):
#         # given
#         current_term = Term()
#         existing_term = Term()

#         # when, then
#         assert are_term_attributes_consistent(None, None, current_term, existing_term, True) is True

#     def test__are_term_attributes_consistent_true(self):
#         # given
#         current_term = Term()
#         current_term.uid = 'test-uid-1'
#         current_term.concept_id = 'test-concept-id-1'

#         existing_term = Term()
#         existing_term.uid = 'test-uid-2'
#         existing_term.concept_id = 'test-concept-id-2'

#         # when, then
#         assert are_term_attributes_consistent(None, None, current_term, existing_term, True) is True

#     def test__are_term_attributes_consistent_different_preferred_term(self):
#         # given
#         current_term = Term()
#         current_term.uid = 'test-uid'
#         current_term.concept_id = 'test-concept-id'
#         current_term.preferred_term = 'test-preferred-term-1'

#         existing_term = Term()
#         existing_term.uid = 'test-uid'
#         existing_term.concept_id = 'test-concept-id'
#         existing_term.preferred_term = 'test-preferred-term-2'

#         # when, then
#         assert are_term_attributes_consistent(None, None, current_term, existing_term, True) is False

#     def test__are_term_attributes_consistent_different_definition(self):
#         # given
#         current_term = Term()
#         current_term.uid = 'test-uid'
#         current_term.concept_id = 'test-concept-id'
#         current_term.preferred_term = 'test-preferred-term'
#         current_term.definition = 'test-definition-1'

#         existing_term = Term()
#         existing_term.uid = 'test-uid'
#         existing_term.concept_id = 'test-concept-id'
#         existing_term.preferred_term = 'test-preferred-term'
#         existing_term.definition = 'test-definition-2'

#         # when, then
#         assert are_term_attributes_consistent(None, None, current_term, existing_term, True) is False

#     def test__are_term_attributes_consistent_different_synonyms(self):
#         # given
#         current_term = Term()
#         current_term.uid = 'test-uid'
#         current_term.concept_id = 'test-concept-id'
#         current_term.preferred_term = 'test-preferred-term'
#         current_term.definition = 'test-definition-1'
#         current_term.synonyms = ['s1', 's2', ' ']

#         existing_term = Term()
#         existing_term.uid = 'test-uid'
#         existing_term.concept_id = 'test-concept-id'
#         existing_term.preferred_term = 'test-preferred-term'
#         existing_term.definition = 'test-definition-2'
#         existing_term.synonyms = ['s1', 's2', '']

#         # when, then
#         assert are_term_attributes_consistent(None, None, current_term, existing_term, True) is False
