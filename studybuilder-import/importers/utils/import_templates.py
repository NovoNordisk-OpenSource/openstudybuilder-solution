clinical_programme = {"name": "string"}

brands = {"name": "string"}

project = {
    "project_number": "string",
    "name": "string",
    "description": "string",
    "clinical_programme_uid": "string",
}

study = {
    "description": "string",
    "study_number": "string",
    "study_acronym": "string",
    "project_number": "string",
}

study_subpart = {
    "description": "string",
    "study_subpart_acronym": "string",
    "study_parent_part_uid": "string",
}

study_patch = {
    "current_metadata": {
        "identification_metadata": {
            "study_number": "string",
            "study_acronym": "string",
            "project_number": "string",
            "project_name": "string",
            "clinical_programme_name": "string",
            "study_id": "string",
            "registry_identifiers": {
                "ct_gov_id": "string",
                "ct_gov_id_null_value_code": {"term_uid": "string", "name": "string"},
                "eudract_id": "string",
                "eudract_id_null_value_code": {"term_uid": "string", "name": "string"},
                "universal_trial_number_utn": "string",
                "universal_trial_number_utn_null_value_code": {
                    "term_uid": "string",
                    "name": "string",
                },
                "japanese_trial_registry_id_japic": "string",
                "japanese_trial_registry_id_japic_null_value_code": {
                    "term_uid": "string",
                    "name": "string",
                },
                "investigational_new_drug_application_number_ind": "string",
                "investigational_new_drug_application_number_ind_null_value_code": {
                    "term_uid": "string",
                    "name": "string",
                },
                "eu_trial_number": "string",
                "eu_trial_number_null_value_code": {
                    "term_uid": "string",
                    "name": "string",
                },
                "civ_id_sin_number": "string",
                "civ_id_sin_number_null_value_code": {
                    "term_uid": "string",
                    "name": "string",
                },
                "national_clinical_trial_number": "string",
                "national_clinical_trial_number_null_value_code": {
                    "term_uid": "string",
                    "name": "string",
                },
                "japanese_trial_registry_number_jrct": "string",
                "japanese_trial_registry_number_jrct_null_value_code": {
                    "term_uid": "string",
                    "name": "string",
                },
                "national_medical_products_administration_nmpa_number": "string",
                "national_medical_products_administration_nmpa_number_null_value_code": {
                    "term_uid": "string",
                    "name": "string",
                },
                "eudamed_srn_number": "string",
                "eudamed_srn_number_null_value_code": {
                    "term_uid": "string",
                    "name": "string",
                },
                "investigational_device_exemption_ide_number": "string",
                "investigational_device_exemption_ide_number_null_value_code": {
                    "term_uid": "string",
                    "name": "string",
                },
            },
        },
        "version_metadata": {
            "study_status": "string",
            "version_number": 0,
            "version_timestamp": "2022-06-10T13:15:22.182Z",
            "version_author": "string",
            "version_description": "string",
        },
        "high_level_study_design": {
            "study_type_code": {"term_uid": "string", "name": "string"},
            "study_type_null_value_code": {"term_uid": "string", "name": "string"},
            "trial_types_codes": [{"term_uid": "string", "name": "string"}],
            "trial_types_null_value_code": {"term_uid": "string", "name": "string"},
            "trial_phase_code": {"term_uid": "string", "name": "string"},
            "trial_phase_null_value_code": {"term_uid": "string", "name": "string"},
            "is_extension_trial": True,
            "is_extension_trial_null_value_code": {
                "term_uid": "string",
                "name": "string",
            },
            "is_adaptive_design": True,
            "is_adaptive_design_null_value_code": {
                "term_uid": "string",
                "name": "string",
            },
            "study_stop_rules": "string",
            "study_stop_rules_null_value_code": {
                "term_uid": "string",
                "name": "string",
            },
            "confirmed_response_minimum_duration": {
                "duration_value": 0,
                "duration_unit_code": {"uid": "string", "name": "string"},
            },
            "confirmed_response_minimum_duration_null_value_code": {
                "term_uid": "string",
                "name": "string",
            },
            "post_auth_indicator": True,
            "post_auth_indicator_null_value_code": {
                "term_uid": "string",
                "name": "string",
            },
        },
        "study_population": {
            "therapeutic_area_codes": [{"term_uid": "string", "name": "string"}],
            "therapeutic_areas_null_value_code": {
                "term_uid": "string",
                "name": "string",
            },
            "disease_conditions_or_indications_codes": [
                {"term_uid": "string", "name": "string"}
            ],
            "disease_conditions_or_indications_null_value_code": {
                "term_uid": "string",
                "name": "string",
            },
            "diagnosis_groups_codes": [{"term_uid": "string", "name": "string"}],
            "diagnosis_groups_null_value_code": {
                "term_uid": "string",
                "name": "string",
            },
            "sex_of_participants_code": {"term_uid": "string", "name": "string"},
            "sex_of_participants_null_value_code": {
                "term_uid": "string",
                "name": "string",
            },
            "rare_disease_indicator": True,
            "rare_disease_indicator_null_value_code": {
                "term_uid": "string",
                "name": "string",
            },
            "healthy_subject_indicator": True,
            "healthy_subject_indicator_null_value_code": {
                "term_uid": "string",
                "name": "string",
            },
            "planned_minimum_age_of_subjects": {
                "duration_value": 0,
                "duration_unit_code": {"uid": "string", "name": "string"},
            },
            "planned_minimum_age_of_subjects_null_value_code": {
                "term_uid": "string",
                "name": "string",
            },
            "planned_maximum_age_of_subjects": {
                "duration_value": 0,
                "duration_unit_code": {"uid": "string", "name": "string"},
            },
            "planned_maximum_age_of_subjects_null_value_code": {
                "term_uid": "string",
                "name": "string",
            },
            "stable_disease_minimum_duration": {
                "duration_value": 0,
                "duration_unit_code": {"uid": "string", "name": "string"},
            },
            "stable_disease_minimum_duration_null_value_code": {
                "term_uid": "string",
                "name": "string",
            },
            "pediatric_study_indicator": True,
            "pediatric_study_indicator_null_value_code": {
                "term_uid": "string",
                "name": "string",
            },
            "pediatric_postmarket_study_indicator": True,
            "pediatric_postmarket_study_indicator_null_value_code": {
                "term_uid": "string",
                "name": "string",
            },
            "pediatric_investigation_plan_indicator": True,
            "pediatric_investigation_plan_indicator_null_value_code": {
                "term_uid": "string",
                "name": "string",
            },
            "relapse_criteria": "string",
            "relapse_criteria_null_value_code": {
                "term_uid": "string",
                "name": "string",
            },
        },
        "study_intervention": {
            "intervention_type_code": {"term_uid": "string", "name": "string"},
            "intervention_type_null_value_code": {
                "term_uid": "string",
                "name": "string",
            },
            "add_on_to_existing_treatments": True,
            "add_on_to_existing_treatments_null_value_code": {
                "term_uid": "string",
                "name": "string",
            },
            "control_type_code": {"term_uid": "string", "name": "string"},
            "control_type_null_value_code": {"term_uid": "string", "name": "string"},
            "intervention_model_code": {"term_uid": "string", "name": "string"},
            "intervention_model_null_value_code": {
                "term_uid": "string",
                "name": "string",
            },
            "is_trial_randomised": True,
            "is_trial_randomised_null_value_code": {
                "term_uid": "string",
                "name": "string",
            },
            "stratification_factor": "string",
            "stratification_factor_null_value_code": {
                "term_uid": "string",
                "name": "string",
            },
            "trial_blinding_schema_code": {"term_uid": "string", "name": "string"},
            "trial_blinding_schema_null_value_code": {
                "term_uid": "string",
                "name": "string",
            },
            "planned_study_length": {
                "duration_value": 0,
                "duration_unit_code": {"uid": "string", "name": "string"},
            },
            "planned_study_length_null_value_code": {
                "term_uid": "string",
                "name": "string",
            },
            "drug_study_indication": True,
            "drug_study_indication_null_value_code": {
                "term_uid": "string",
                "name": "string",
            },
            "device_study_indication": "string",
            "device_study_indication_null_value_code": {
                "term_uid": "string",
                "name": "string",
            },
            "trial_intent_types_codes": [{"term_uid": "string", "name": "string"}],
            "trial_intent_types_null_value_code": {
                "term_uid": "string",
                "name": "string",
            },
        },
        "study_description": {"study_title": "string"},
    }
}

study_arm = {
    "name": "string",
    "short_name": "string",
    "code": "string",
    "description": "string",
    "arm_colour": "string",
    "randomization_group": "string",
    "number_of_subjects": 0,
    "arm_type_uid": "string",
}

study_cohort = {
    "name": "string",
    "short_name": "string",
    "code": "string",
    "description": "string",
    "colour_code": "string",
    "number_of_subjects": 0,
    "branch_arm_uids": ["string"],
    "arm_uids": ["string"],
}

study_element = {
    "name": "string",
    "short_name": "string",
    "code": "string",
    "description": "string",
    "planned_duration": {
        "duration_value": 0,
        "duration_unit_code": {"uid": "string", "name": "string"},
    },
    "start_rule": "string",
    "end_rule": "string",
    "element_colour": "string",
    "element_subtype_uid": "string",
}

study_epoch = {
    "study_uid": "string",
    "start_rule": "string",
    "end_rule": "string",
    "epoch": "string",
    "epoch_subtype": "string",
    "duration_unit": "string",
    "order": 0,
    "description": "string",
    "duration": 0,
    "color_hash": "string",
}

study_visit = {
    "study_epoch_uid": "string",
    "visit_type_uid": "string",
    "time_reference_uid": "string",
    "time_value": 0,
    "time_unit_uid": "string",
    "visit_sublabel_codelist_uid": "string",
    "visit_sublabel_reference": "string",
    "consecutive_visit_group": "string",
    "show_visit": True,
    "min_visit_window_value": 0,
    "max_visit_window_value": 0,
    "visit_window_unit_uid": "string",
    "description": "string",
    "start_rule": "string",
    "end_rule": "string",
    "visit_contact_mode_uid": "string",
    "epoch_allocation_uid": "string",
    "visit_class": "string",
    "visit_subclass": "string",
    "is_global_anchor_visit": False,
    "is_soa_milestone": False,
    "visit_name": None,
    "visit_short_name": None,
    "visit_number": None,
    "unique_visit_number": None,
    "repeating_frequency_uid": None,
}

study_design_cell = {
    "study_arm_uid": "string",
    "study_epoch_uid": "string",
    "study_element_uid": "string",
    "transition_rule": "string",
    "order": 0,
}

study_branch = {
    "name": "string",
    "short_name": "string",
    "code": "string",
    "description": "string",
    "colour_code": "string",
    "randomization_group": "string",
    "number_of_subjects": 0,
    "arm_uid": "string",
}

study_activity = {
    "soa_group_term_uid": "string",
    "activity_uid": "string",
    "activity_subgroup_uid": "string",
    "activity_group_uid": "string",
    "activity_instance_uid": "string",
}

objective_template = {
    "name": "string",
    "guidance_text": "string",
    "study_uid": "string",
    "library_name": "string",
    "default_parameter_terms": [
        {
            "position": 0,
            "conjunction": "string",
            "terms": [
                {"uid": "string", "name": "string", "type": "string", "index": 0}
            ],
        }
    ],
    "indication_uids": ["string"],
    "is_confirmatory_testing": True,
    "category_uids": ["string"],
}

objective_preinstance = {
    "parameter_terms": [
        {
            "terms": [
                {"uid": "string", "name": "string", "type": "string", "index": 0}
            ],
            "value": 0,
            "conjunction": "string",
        }
    ],
    "library_name": "string",
    "is_confirmatory_testing": True,
    "indication_uids": ["string"],
    "category_uids": ["string"],
}

criteria_template = {
    "name": "string",
    "guidance_text": "string",
    "study_uid": "string",
    "library_name": "string",
    "default_parameter_terms": [
        {
            "position": 0,
            "conjunction": "string",
            "terms": [
                {"uid": "string", "name": "string", "type": "string", "index": 0}
            ],
        }
    ],
    "type_uid": "string",
    "indication_uids": ["string"],
    "category_uids": ["string"],
    "sub_category_uids": ["string"],
}

criteria_preinstance = {
    "parameter_terms": [
        {
            "terms": [
                {"uid": "string", "name": "string", "type": "string", "index": 0}
            ],
            "value": 0,
            "conjunction": "string",
        }
    ],
    "library_name": "string",
    "indication_uids": ["string"],
    "category_uids": ["string"],
    "sub_category_uids": ["string"],
}

timeframe_template = {
    "name": "string",
    "guidance_text": "string",
    "library_name": "string",
}

endpoint_template = {
    "name": "string",
    "guidance_text": "string",
    "study_uid": "string",
    "library_name": "string",
    "default_parameter_terms": [
        {
            "position": 0,
            "conjunction": "string",
            "terms": [
                {"uid": "string", "name": "string", "type": "string", "index": 0}
            ],
        }
    ],
    "indication_uids": ["string"],
    "category_uids": ["string"],
    "sub_category_uids": ["string"],
}

endpoint_preinstance = {
    "parameter_terms": [
        {
            "terms": [
                {"uid": "string", "name": "string", "type": "string", "index": 0}
            ],
            "value": 0,
            "conjunction": "string",
        }
    ],
    "library_name": "string",
    "indication_uids": ["string"],
    "category_uids": ["string"],
    "sub_category_uids": ["string"],
}

footnote_template = {
    "name": "string",
    "study_uid": "string",
    "library_name": "string",
    "default_parameter_terms": [
        {
            "position": 0,
            "conjunction": "string",
            "terms": [
                {"uid": "string", "name": "string", "type": "string", "index": 0}
            ],
        }
    ],
    "type_uid": "string",
    "indication_uids": ["string"],
    "activity_uids": ["string"],
    "activity_group_uids": ["string"],
    "activity_subgroup_uids": ["string"],
}

footnote_preinstance = {
    "parameter_terms": [
        {
            "terms": [
                {"uid": "string", "name": "string", "type": "string", "index": 0}
            ],
            "value": 0,
            "conjunction": "string",
        }
    ],
    "library_name": "string",
    "indication_uids": ["string"],
    "activity_uids": ["string"],
    "activity_group_uids": ["string"],
    "activity_subgroup_uids": ["string"],
}

activity_instruction_template = {
    "name": "string",
    "guidance_text": "string",
    "library_name": "string",
    "default_parameter_terms": [
        {
            "position": 0,
            "conjunction": "string",
            "terms": [
                {"uid": "string", "name": "string", "type": "string", "index": 0}
            ],
        }
    ],
    "indication_uids": ["string"],
    "activity_uids": ["string"],
    "activity_group_uids": ["string"],
    "activity_subgroup_uids": ["string"],
}

activity_instruction_preinstance = {
    "parameter_terms": [
        {
            "terms": [
                {"uid": "string", "name": "string", "type": "string", "index": 0}
            ],
            "value": 0,
            "conjunction": "string",
        }
    ],
    "library_name": "string",
    "indication_uids": ["string"],
    "activity_uids": ["string"],
    "activity_group_uids": ["string"],
    "activity_subgroup_uids": ["string"],
}

study_objective = {
    "objective_level_uid": "string",
    "objective_data": {
        "parameter_terms": [
            {
                "terms": [
                    {"uid": "string", "name": "string", "type": "string", "index": 0}
                ],
                "value": 0,
                "conjunction": "string",
            }
        ],
        "objective_template_uid": "string",
        "library_name": "string",
    },
}


study_endpoint = {
    "study_objective_uid": "string",
    "endpoint_level_uid": "string",
    "endpoint_sublevel_uid": "string",
    "endpoint_data": {
        "parameter_terms": [
            {
                "terms": [
                    {"uid": "string", "name": "string", "type": "string", "index": 0}
                ],
                "value": 0,
                "conjunction": "string",
            }
        ],
        "endpoint_template_uid": "string",
        "library_name": "string",
    },
    "endpoint_units": {"units": ["string"], "separator": "string"},
    "timeframe_uid": "string",
}

study_criteria = {
    "criteria_data": {
        "parameter_terms": [
            {
                "terms": [
                    {"uid": "string", "name": "string", "type": "string", "index": 0}
                ],
                "value": 0,
                "conjunction": "string",
            }
        ],
        "criteria_template_uid": "string",
        "library_name": "string",
    }
}

study_activity_schedule = {
    "study_activity_uid": "string",
    "study_visit_uid": "string",
    "note": "string",
}

timeframes = {
    "parameter_terms": [
        {
            "terms": [
                {"uid": "string", "name": "string", "type": "string", "index": 0}
            ],
            "position": 0,
            "value": 0,
            "conjunction": "string",
        }
    ],
    "timeframe_template_uid": "string",
    "name_override": "string",
    "library_name": "string",
}

compound_alias = {
    "name": "string",
    "name_sentence_case": "string",
    "definition": "string",
    "abbreviation": "string",
    "library_name": "string",
    "compound_uid": "string",
    "is_preferred_synonym": False,
}

compound = {
    "name": "string",
    "name_sentence_case": "string",
    "definition": "string",
    "abbreviation": "string",
    "library_name": "string",
    "analyte_number": "string",
    "nnc_short_number": "string",
    "nnc_long_number": "string",
    "is_sponsor_compound": True,
    "is_name_inn": True,
    "substance_terms_uids": [],
    "dose_values_uids": [],
    "strength_values_uids": [],
    "lag_times_uids": [],
    "delivery_devices_uids": [],
    "dispensers_uids": [],
    "projects_uids": [],
    "brands_uids": [],
    "dose_frequency_uids": [],
    "dosage_form_uids": [],
    "route_of_administration_uids": [],
    "half_life_uid": "string",
}

active_substance = {
    "external_id": "string",
    "analyte_number": "string",
    "short_number": "string",
    "long_number": "string",
    "inn": "string",
    "library_name": "string",
    "unii_term_uid": "string",
}

pharmaceutical_product = {
    "external_id": "string",
    "library_name": "string",
    "dosage_form_uids": [],
    "route_of_administration_uids": [],
    "formulations": [],
}

formulation = {
    "external_id": "string",
    "name": "string",
    "ingredients": [],
}

ingredient = {
    "active_substance_uid": "string",
    "formulation_name": "string",
    "external_id": "string",
    "strength_uid": "string",
    "half_life_uid": "string",
    "lag_time_uids": [],
}

medicinal_product = {
    "external_id": "string",
    "name": "string",
    "name_sentence_case": "string",
    "library_name": "string",
    "dose_value_uids": [],
    "dose_frequency_uid": "string",
    "delivery_device_uid": "string",
    "dispenser_uid": "string",
    "compound_uid": "string",
    "pharmaceutical_product_uids": [],
}

numeric_value = {
    "name": "string",
    "name_sentence_case": "string",
    "definition": "string",
    "abbreviation": "string",
    "library_name": "string",
    "template_parameter": False,
    "value": 0,
}

numeric_value_with_unit = {
    "name": "string",
    "name_sentence_case": "string",
    "definition": "string",
    "abbreviation": "string",
    "library_name": "string",
    "template_parameter": False,
    "value": 0,
    "unit_definition_uid": "string",
}

text_value = {
    "name": "string",
    "name_sentence_case": "string",
    "definition": "string",
    "abbreviation": "string",
    "library_name": "string",
    "template_parameter": False,
}

visit_name = {
    "name": "string",
    "name_sentence_case": "string",
    "definition": "string",
    "abbreviation": "string",
    "library_name": "string",
    "template_parameter": False,
}

study_day = {
    "name": "string",
    "name_sentence_case": "string",
    "definition": "string",
    "abbreviation": "string",
    "library_name": "string",
    "template_parameter": False,
    "value": 0,
}

study_week = {
    "name": "string",
    "name_sentence_case": "string",
    "definition": "string",
    "abbreviation": "string",
    "library_name": "string",
    "template_parameter": False,
    "value": 0,
}

study_duration_days = {
    "name": "string",
    "name_sentence_case": "string",
    "definition": "string",
    "abbreviation": "string",
    "library_name": "string",
    "template_parameter": False,
    "value": 0,
}

study_duration_weeks = {
    "name": "string",
    "name_sentence_case": "string",
    "definition": "string",
    "abbreviation": "string",
    "library_name": "string",
    "template_parameter": False,
    "value": 0,
}

time_point = {
    "name": "string",
    "name_sentence_case": "string",
    "definition": "string",
    "abbreviation": "string",
    "library_name": "string",
    "template_parameter": False,
    "numeric_value_uid": "string",
    "unit_definition_uid": "string",
    "time_reference_uid": "string",
}

lag_time = {
    "name": "string",
    "name_sentence_case": "string",
    "definition": "string",
    "abbreviation": "string",
    "library_name": "string",
    "template_parameter": False,
    "value": 0,
    "unit_definition_uid": "string",
    "sdtm_domain_uid": "string",
}

study_compound = {
    "compound_alias_uid": "string",
    "type_of_treatment_uid": "string",
    "medicinal_product_uid": "string",
    "other_info": "string",
    "reason_for_missing_null_value_uid": "string",
}

unit_definition = {
    "name": "string",
    "library_name": "Sponsor",
    "convertible_unit": True,
    "display_unit": True,
    "master_unit": True,
    "si_unit": True,
    "us_conventional_unit": True,
    "ct_units": ["string"],
    "unit_subsets": [],
    "ucum": "string",
    "unit_dimension": "string",
    "legacy_code": "string",
    "molecular_weight_conv_expon": 0,
    "conversion_factor_to_master": 0,
    "comment": "string",
    "order": 0,
    "definition": "string",
    "template_parameter": False,
}

activity = {
    "name": "string",
    "name_sentence_case": "string",
    "definition": "string",
    "abbreviation": "string",
    "library_name": "string",
    "activity_groupings": [
        {"activity_group_uid": "string", "activity_subgroup_uid": "string"}
    ],
}

activity_groups = {
    "name": "string",
    "name_sentence_case": "string",
    "definition": "string",
    "abbreviation": "string",
    "library_name": "string",
}

activity_subgroups = {
    "name": "string",
    "name_sentence_case": "string",
    "definition": "string",
    "abbreviation": "string",
    "library_name": "string",
    "activity_groups": [],
}

ct_term = {
    "catalogue_name": "string",
    "codelist_uid": "string",
    "code_submission_value": "string",
    "name_submission_value": "string",
    "nci_preferred_name": "string",
    "definition": "string",
    "sponsor_preferred_name": "string",
    "sponsor_preferred_name_sentence_case": "string",
    "order": None,
    "library_name": "string",
}

dictionary_term = {
    "dictionary_id": "string",
    "name": "string",
    "name_sentence_case": "string",
    "abbreviation": "string",
    "definition": "string",
    "codelist_uid": "string",
    "library_name": "string",
}
