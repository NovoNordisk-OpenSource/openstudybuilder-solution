Feature: All API endpoints can be called successfully

  @impact:api
  Scenario Outline: Endpoints that take a series of parameters return with ok status
    Given the API is reachable
    Then the endpoint <url> called with a list of <parameters> returns successfully

    Examples:
      | url                                                        | parameters                                                                                      |
      | /activity-instance-classes                                 | <none>                                                                                          |
      | /activity-instance-classes/headers                         | field_name=name                                                                                 |
      | /activity-instruction-pre-instances                        | <none>                                                                                          |
      | /activity-instruction-pre-instances/audit-trail            | <none>                                                                                          |
      | /activity-instruction-pre-instances/headers                | field_name=name                                                                                 |
      | /activity-instruction-templates                            | <none>                                                                                          |
      | /activity-instruction-templates/audit-trail                | <none>                                                                                          |
      | /activity-instruction-templates/headers                    | field_name=name                                                                                 |
      | /activity-instructions                                     | <none>                                                                                          |
      | /activity-instructions/audit-trail                         | <none>                                                                                          |
      | /activity-instructions/headers                             | field_name=name                                                                                 |
      | /activity-item-classes                                     | <none>                                                                                          |
      | /activity-item-classes/headers                             | field_name=name                                                                                 |
      | /admin/caches                                              | <none>                                                                                          |
      | /brands                                                    | <none>                                                                                          |
      | /clinical-programmes                                       | <none>                                                                                          |
      | /clinical-programmes/headers                               | field_name=name                                                                                 |
      | /comment-threads                                           | <none>                                                                                          |
      | /comment-topics                                            | <none>                                                                                          |
      | /concepts/active-substances                                | <none>                                                                                          |
      | /concepts/active-substances/headers                        | field_name=uid                                                                                  |
      | /concepts/active-substances/versions                       | <none>                                                                                          |
      | /concepts/activities/activities                            | <none>                                                                                          |
      | /concepts/activities/activities/headers                    | field_name=name                                                                                 |
      | /concepts/activities/activities/versions                   | <none>                                                                                          |
      | /concepts/activities/activity-groups                       | <none>                                                                                          |
      | /concepts/activities/activity-groups/headers               | field_name=name                                                                                 |
      | /concepts/activities/activity-groups/versions              | <none>                                                                                          |
      | /concepts/activities/activity-instances                    | <none>                                                                                          |
      | /concepts/activities/activity-instances/headers            | field_name=name                                                                                 |
      | /concepts/activities/activity-instances/attributes/versions | <none>                                                                                         |
      | /concepts/activities/activity-sub-groups                   | <none>                                                                                          |
      | /concepts/activities/activity-sub-groups/headers           | field_name=name                                                                                 |
      | /concepts/activities/activity-sub-groups/versions          | <none>                                                                                          |
      | /concepts/compound-aliases                                 | <none>                                                                                          |
      | /concepts/compound-aliases/headers                         | field_name=name                                                                                 |
      | /concepts/compound-aliases/versions                        | <none>                                                                                          |
      | /concepts/compounds                                        | <none>                                                                                          |
      | /concepts/compounds-simple                                 | <none>                                                                                          |
      | /concepts/compounds/headers                                | field_name=name                                                                                 |
      | /concepts/compounds/versions                               | <none>                                                                                          |
      | /concepts/lag-times                                        | <none>                                                                                          |
      | /concepts/lag-times/headers                                | field_name=name                                                                                 |
      | /concepts/medicinal-products                               | <none>                                                                                          |
      | /concepts/medicinal-products/headers                       | field_name=uid                                                                                  |
      | /concepts/medicinal-products/versions                      | <none>                                                                                          |
      | /concepts/numeric-values                                   | <none>                                                                                          |
      | /concepts/numeric-values-with-unit                         | <none>                                                                                          |
      | /concepts/numeric-values-with-unit/headers                 | field_name=name                                                                                 |
      | /concepts/numeric-values/headers                           | field_name=name                                                                                 |
      | /odms/metadata/aliases                                     | <none>                                                                                          |
      | /odms/metadata/translated-texts                            | <none>                                                                                          |
      | /odms/metadata/formal-expressions                          | <none>                                                                                          |
      | /odms/metadata/xmls/stylesheets                            | <none>                                                                                          |
      | /odms/conditions                                           | <none>                                                                                          |
      | /odms/conditions/headers                                   | field_name=name                                                                                 |
      | /odms/forms                                                | <none>                                                                                          |
      | /odms/forms/headers                                        | field_name=name                                                                                 |
      | /odms/forms/study-events                                   | <none>                                                                                          |
      | /odms/item-groups                                          | <none>                                                                                          |
      | /odms/item-groups/forms                                    | <none>                                                                                          |
      | /odms/item-groups/headers                                  | field_name=name                                                                                 |
      | /odms/items                                                | <none>                                                                                          |
      | /odms/items/headers                                        | field_name=name                                                                                 |
      | /odms/items/item-groups                                    | <none>                                                                                          |
      | /odms/metadata/xmls/stylesheets                            | <none>                                                                                          |
      | /odms/methods                                              | <none>                                                                                          |
      | /odms/methods/headers                                      | field_name=name                                                                                 |
      | /odms/study-events                                         | <none>                                                                                          |
      | /odms/study-events/headers                                 | field_name=name                                                                                 |
      | /odms/vendor-attributes                                    | <none>                                                                                          |
      | /odms/vendor-attributes/headers                            | field_name=name                                                                                 |
      | /odms/vendor-elements                                      | <none>                                                                                          |
      | /odms/vendor-elements/headers                              | field_name=name                                                                                 |
      | /odms/vendor-namespaces                                    | <none>                                                                                          |
      | /odms/vendor-namespaces/headers                            | field_name=name                                                                                 |
      | /concepts/pharmaceutical-products                          | <none>                                                                                          |
      | /concepts/pharmaceutical-products/headers                  | field_name=uid                                                                                  |
      | /concepts/pharmaceutical-products/versions                 | <none>                                                                                          |
      | /concepts/study-days                                       | <none>                                                                                          |
      | /concepts/study-days/headers                               | field_name=name                                                                                 |
      | /concepts/study-duration-days                              | <none>                                                                                          |
      | /concepts/study-duration-days/headers                      | field_name=name                                                                                 |
      | /concepts/study-duration-weeks                             | <none>                                                                                          |
      | /concepts/study-duration-weeks/headers                     | field_name=name                                                                                 |
      | /concepts/study-weeks                                      | <none>                                                                                          |
      | /concepts/study-weeks/headers                              | field_name=name                                                                                 |
      | /concepts/text-values                                      | <none>                                                                                          |
      | /concepts/text-values/headers                              | field_name=name                                                                                 |
      | /concepts/time-points                                      | <none>                                                                                          |
      | /concepts/time-points/headers                              | field_name=name                                                                                 |
      | /concepts/unit-definitions                                 | <none>                                                                                          |
      | /concepts/unit-definitions/headers                         | field_name=name                                                                                 |
      | /concepts/visit-names                                      | <none>                                                                                          |
      | /concepts/visit-names/headers                              | field_name=name                                                                                 |
      | /configurations                                            | <none>                                                                                          |
      | /criteria                                                  | <none>                                                                                          |
      | /criteria-pre-instances                                    | <none>                                                                                          |
      | /criteria-pre-instances/audit-trail                        | <none>                                                                                          |
      | /criteria-pre-instances/headers                            | field_name=name                                                                                 |
      | /criteria-templates                                        | <none>                                                                                          |
      | /criteria-templates/audit-trail                            | <none>                                                                                          |
      | /criteria-templates/headers                                | field_name=name                                                                                 |
      | /criteria/audit-trail                                      | <none>                                                                                          |
      | /criteria/headers                                          | field_name=name                                                                                 |
      | /ct/catalogues                                             | <none>                                                                                          |
      | /ct/codelists                                              | <none>                                                                                          |
      | /ct/codelists/attributes                                   | <none>                                                                                          |
      | /ct/codelists/attributes/headers                           | field_name=catalogue_names                                                                      |
      | /ct/codelists/headers                                      | field_name=name.name                                                                            |
      | /ct/codelists/terms                                        | codelist_uid={codelist_uid}                                                                     |
      | /ct/codelists/terms/headers                                | codelist_uid={codelist_uid}, field_name=term_uid                                                |
      | /ct/codelists/names                                        | <none>                                                                                          |
      | /ct/codelists/names/headers                                | field_name=name                                                                                 |
      | /ct/codelists/{codelist_uid}/attributes                    | <none>                                                                                          |
      | /ct/codelists/{codelist_uid}/attributes/versions           | <none>                                                                                          |
      | /ct/codelists/{codelist_uid}/names                         | <none>                                                                                          |
      | /ct/codelists/{codelist_uid}/names/versions                | <none>                                                                                          |
      | /ct/codelists/{codelist_uid}/sub-codelists                 | term_uids=CTTerm_000001                                                                         |
      | /ct/codelists/{codelist_uid}/terms                         | term_uids=CTTerm_000001                                                                         |
      | /ct/codelists/{codelist_uid}/paired                        | <none>                                                                                          |
      | /ct/packages                                               | <none>                                                                                          |
      | /ct/packages/changes                                       | catalogue_name=SDTM CT, old_package_date=2014-09-26, new_package_date=2014-12-19                |
      | /ct/packages/dates                                         | catalogue_name=SDTM CT                                                                          |
      | /ct/packages/{codelist_uid}/changes                        | catalogue_name=SDTM CT, old_package_date=2014-09-26, new_package_date=2014-12-19                |
      | /ct/stats                                                  | <none>                                                                                          |
      | /ct/terms                                                  | <none>                                                                                          |
      | /ct/terms/attributes                                       | <none>                                                                                          |
      | /ct/terms/attributes/headers                               | field_name=term_uid                                                                             |
      | /ct/terms/headers                                          | field_name=catalogue_names                                                                      |
      | /ct/terms/names                                            | <none>                                                                                          |
      | /ct/terms/names/headers                                    | field_name=term_uid                                                                             |
      | /ct/terms/{term_uid}/attributes                            | <none>                                                                                          |
      | /ct/terms/{term_uid}/attributes/versions                   | <none>                                                                                          |
      | /ct/terms/{term_uid}/names                                 | <none>                                                                                          |
      | /ct/terms/{term_uid}/names/versions                        | <none>                                                                                          |
      | /ct/terms/{term_uid}/codelists                             | <none>                                                                                          |
      | /ct/terms/{term_uid}/parents                               | <none>                                                                                          |
      | /usdm/v4/studyDefinitions/{study_uid}                      | <none>                                                                                          |
      | /usdm/v4/studyDefinitions/{study_uid}/m11                  | <none>                                                                                          |
      | /dictionaries/codelists                                    | library_name=SNOMED                                                                             |
      | /dictionaries/codelists/headers                            | field_name=name, library_name=SNOMED                                                            |
      | /dictionaries/substances                                   | <none>                                                                                          |
      | /dictionaries/terms                                        | codelist_uid={codelist_uid}                                                                     |
      | /dictionaries/terms/headers                                | field_name=name, codelist_uid={codelist_uid}                                                    |
      | /endpoint-pre-instances                                    | <none>                                                                                          |
      | /endpoint-pre-instances/audit-trail                        | <none>                                                                                          |
      | /endpoint-pre-instances/headers                            | field_name=name                                                                                 |
      | /endpoint-templates                                        | <none>                                                                                          |
      | /endpoint-templates/audit-trail                            | <none>                                                                                          |
      | /endpoint-templates/headers                                | field_name=name                                                                                 |
      | /endpoints                                                 | <none>                                                                                          |
      | /endpoints/audit-trail                                     | <none>                                                                                          |
      | /endpoints/headers                                         | field_name=name                                                                                 |
      | /epochs/allowed-configs                                    | <none>                                                                                          |
      | /footnote-pre-instances                                    | <none>                                                                                          |
      | /footnote-pre-instances/audit-trail                        | <none>                                                                                          |
      | /footnote-pre-instances/headers                            | field_name=name                                                                                 |
      | /footnote-templates                                        | <none>                                                                                          |
      | /footnote-templates/audit-trail                            | <none>                                                                                          |
      | /footnote-templates/headers                                | field_name=name                                                                                 |
      | /footnotes                                                 | <none>                                                                                          |
      | /footnotes/audit-trail                                     | <none>                                                                                          |
      | /footnotes/headers                                         | field_name=name                                                                                 |
      | /libraries                                                 | <none>                                                                                          |
      | /listings/libraries/all/gcmd/cdisc-ct-list                 | <none>                                                                                          |
      | /listings/libraries/all/gcmd/cdisc-ct-list/headers         | field_name=name                                                                                 |
      | /listings/libraries/all/gcmd/cdisc-ct-pkg                  | <none>                                                                                          |
      | /listings/libraries/all/gcmd/cdisc-ct-pkg/headers          | field_name=name                                                                                 |
      | /listings/libraries/all/gcmd/cdisc-ct-ver                  | <none>                                                                                          |
      | /listings/libraries/all/gcmd/cdisc-ct-ver/headers          | field_name=name                                                                                 |
      | /listings/libraries/all/gcmd/topic-cd-def                  | <none>                                                                                          |
      | /listings/libraries/all/gcmd/topic-cd-def/headers          | field_name=name                                                                                 |
      | /listings/metadata                                         | <none>                                                                                          |
      | /listings/metadata/headers                                 | field_name=name                                                                                 |
      | /listings/studies/{study_uid}/adam/mdendpnt                | <none>                                                                                          |
      | /listings/studies/{study_uid}/adam/mdendpnt/headers        | field_name=OBJTVLVL                                                                             |
      | /listings/studies/{study_uid}/adam/mdvisit                 | <none>                                                                                          |
      | /listings/studies/{study_uid}/adam/mdvisit/headers         | field_name=VISTPCD                                                                              |
      | /listings/studies/{study_uid}/sdtm/ta                      | <none>                                                                                          |
      | /listings/studies/{study_uid}/sdtm/tdm                     | <none>                                                                                          |
      | /listings/studies/{study_uid}/sdtm/te                      | <none>                                                                                          |
      | /listings/studies/{study_uid}/sdtm/ti                      | <none>                                                                                          |
      | /listings/studies/{study_uid}/sdtm/ts                      | <none>                                                                                          |
      | /listings/studies/{study_uid}/sdtm/tv                      | <none>                                                                                          |
      | /objective-pre-instances                                   | <none>                                                                                          |
      | /objective-pre-instances/audit-trail                       | <none>                                                                                          |
      | /objective-pre-instances/headers                           | field_name=name                                                                                 |
      | /objective-templates                                       | <none>                                                                                          |
      | /objective-templates/audit-trail                           | <none>                                                                                          |
      | /objective-templates/headers                               | field_name=name                                                                                 |
      | /objectives                                                | <none>                                                                                          |
      | /objectives/audit-trail                                    | <none>                                                                                          |
      | /objectives/headers                                        | field_name=name                                                                                 |
      | /projects                                                  | <none>                                                                                          |
      | /projects/headers                                          | field_name=name                                                                                 |
      | /standards/class-variables                                 | data_model_name=SDTM, data_model_version=2.0, dataset_class_name=Demographics                   |
      | /standards/class-variables/headers                         | data_model_name=SDTM, data_model_version=2.0, dataset_class_name=Demographics, field_name=label |
      | /standards/data-model-igs                                  | <none>                                                                                          |
      | /standards/data-model-igs/headers                          | field_name=name                                                                                 |
      | /standards/data-models                                     | <none>                                                                                          |
      | /standards/data-models/headers                             | field_name=name                                                                                 |
      | /standards/dataset-classes                                 | data_model_name=SDTM                                                                            |
      | /standards/dataset-classes/headers                         | data_model_name=SDTM, field_name=uid                                                            |
      | /standards/dataset-scenarios                               | data_model_ig_name=SDTMIG, data_model_ig_version=2.0                                            |
      | /standards/dataset-scenarios/headers                       | data_model_ig_name=SDTMIG, data_model_ig_version=2.0, field_name=label                          |
      | /standards/dataset-variables                               | data_model_ig_name=SDTMIG, data_model_ig_version=3.2                                            |
      | /standards/dataset-variables/headers                       | data_model_ig_name=SDTMIG, data_model_ig_version=3.2, field_name=label                          |
      | /standards/datasets                                        | data_model_ig_name=SDTMIG, data_model_ig_version=3.2                                            |
      | /standards/datasets/headers                                | data_model_ig_name=SDTMIG, data_model_ig_version=3.2, field_name=label                          |
      | /standards/sponsor-models/dataset-variables                | <none>                                                                                          |
      | /standards/sponsor-models/dataset-variables/headers        | data_model_ig_name=SDTMIG, data_model_ig_version=3.2, field_name=label                          |
      | /standards/sponsor-models/datasets                         | <none>                                                                                          |
      | /standards/sponsor-models/datasets/headers                 | field_name=xml_title                                                                            |
      | /standards/sponsor-models/models                           | <none>                                                                                          |
      | /standards/sponsor-models/models/headers                   | field_name=name                                                                                 |
      | /studies                                                   | <none>                                                                                          |
      | /studies/headers                                           | field_name=name                                                                                 |
      | /studies/list                                              | <none>                                                                                          |
      | /studies/list                                              | minimal_response=false                                                                          |
      | /studies/structure-overview                                | <none>                                                                                          |
      | /studies/structure-overview/headers                        | field_name=study_ids                                                                            |
      | /studies/{study_uid}                                       | <none>                                                                                          |
      | /studies/{study_uid}/allowed-consecutive-groups            | <none>                                                                                          |
      | /studies/{study_uid}/anchor-visits-for-special-visit       | study_epoch_uid=StudyEpoch_000021                                                               |
      | /studies/{study_uid}/anchor-visits-in-group-of-subvisits   | <none>                                                                                          |
      | /studies/{study_uid}/audit-trail                           | <none>                                                                                          |
      | /studies/{study_uid}/ctr/odm.xml                           | <none>                                                                                          |
      | /studies/{study_uid}/design.svg                            | <none>                                                                                          |
      | /studies/{study_uid}/detailed-soa-exports                  | <none>                                                                                          |
      | /studies/{study_uid}/detailed-soa-history                  | <none>                                                                                          |
      | /studies/{study_uid}/fields-audit-trail                    | <none>                                                                                          |
      | /studies/{study_uid}/flowchart                             | <none>                                                                                          |
      | /studies/{study_uid}/flowchart                             | layout=protocol                                                                                 |
      | /studies/{study_uid}/flowchart                             | layout=protocol_lab_table                                                                       |
      | /studies/{study_uid}/flowchart                             | layout=detailed                                                                                 |
      | /studies/{study_uid}/flowchart                             | layout=operational                                                                              |
      | /studies/{study_uid}/flowchart.docx                        | <none>                                                                                          |
      | /studies/{study_uid}/flowchart.docx                        | layout=protocol                                                                                 |
      | /studies/{study_uid}/flowchart.docx                        | layout=detailed                                                                                 |
      | /studies/{study_uid}/flowchart.docx                        | layout=operational                                                                              |
      | /studies/{study_uid}/flowchart.html                        | <none>                                                                                          |
      | /studies/{study_uid}/flowchart.html                        | layout=protocol                                                                                 |
      | /studies/{study_uid}/flowchart.html                        | layout=protocol, include_uids=true                                                              |
      | /studies/{study_uid}/flowchart.html                        | layout=protocol_lab_table                                                                       |
      | /studies/{study_uid}/flowchart.html                        | layout=protocol_lab_table, include_uids=true                                                    |
      | /studies/{study_uid}/flowchart.html                        | layout=detailed                                                                                 |
      | /studies/{study_uid}/flowchart.html                        | layout=operational                                                                              |
      | /studies/{study_uid}/flowchart/coordinates                 | <none>                                                                                          |
      | /studies/{study_uid}/interventions                         | <none>                                                                                          |
      | /studies/{study_uid}/interventions.docx                    | <none>                                                                                          |
      | /studies/{study_uid}/interventions.html                    | <none>                                                                                          |
      | /studies/{study_uid}/operational-soa-exports               | <none>                                                                                          |
      | /studies/{study_uid}/operational-soa.html                  | <none>                                                                                          |
      | /studies/{study_uid}/operational-soa.xlsx                  | <none>                                                                                          |
      | /studies/{study_uid}/pharma-cm                             | <none>                                                                                          |
      | /studies/{study_uid}/pharma-cm.xml                         | <none>                                                                                          |
      | /studies/{study_uid}/protocol-soa-exports                  | <none>                                                                                          |
      | /studies/{study_uid}/protocol-title                        | <none>                                                                                          |
      | /studies/{study_uid}/snapshot-history                      | <none>                                                                                          |
      | /studies/{study_uid}/soa-preferences                       | <none>                                                                                          |
      | /studies/{study_uid}/study-activities                      | <none>                                                                                          |
      | /studies/{study_uid}/study-activities/audit-trail          | <none>                                                                                          |
      | /studies/{study_uid}/study-activities/headers              | field_name=name                                                                                 |
      | /studies/{study_uid}/study-activity-groups                 | <none>                                                                                          |
      | /studies/{study_uid}/study-activity-instances              | <none>                                                                                          |
      | /studies/{study_uid}/study-activity-instances/audit-trail  | <none>                                                                                          |
      | /studies/{study_uid}/study-activity-instances/headers      | field_name=activity                                                                             |
      | /studies/{study_uid}/study-activity-instructions           | <none>                                                                                          |
      | /studies/{study_uid}/study-activity-schedules              | <none>                                                                                          |
      | /studies/{study_uid}/study-activity-schedules/audit-trail/ | <none>                                                                                          |
      | /studies/{study_uid}/study-activity-subgroups              | <none>                                                                                          |
      | /studies/{study_uid}/study-arms                            | <none>                                                                                          |
      | /studies/{study_uid}/study-arms/audit-trail                | <none>                                                                                          |
      | /studies/{study_uid}/study-arms/headers                    | field_name=name                                                                                 |
      | /studies/{study_uid}/study-branch-arm/audit-trail          | <none>                                                                                          |
      | /studies/{study_uid}/study-branch-arms                     | <none>                                                                                          |
      | /studies/{study_uid}/study-cohort/audit-trail              | <none>                                                                                          |
      | /studies/{study_uid}/study-cohorts                         | <none>                                                                                          |
      | /studies/{study_uid}/study-compound-dosings                | <none>                                                                                          |
      | /studies/{study_uid}/study-compound-dosings/audit-trail    | <none>                                                                                          |
      | /studies/{study_uid}/study-compound-dosings/headers        | field_name=name                                                                                 |
      | /studies/{study_uid}/study-compounds                       | <none>                                                                                          |
      | /studies/{study_uid}/study-compounds/audit-trail           | <none>                                                                                          |
      | /studies/{study_uid}/study-compounds/headers               | field_name=name                                                                                 |
      | /studies/{study_uid}/study-criteria                        | <none>                                                                                          |
      | /studies/{study_uid}/study-criteria/audit-trail            | <none>                                                                                          |
      | /studies/{study_uid}/study-criteria/headers                | field_name=name                                                                                 |
      | /studies/{study_uid}/study-design-cells                    | <none>                                                                                          |
      | /studies/{study_uid}/study-design-cells/arm/{arm_uid}      | <none>                                                                                          |
      | /studies/{study_uid}/study-design-cells/audit-trail/       | <none>                                                                                          |
      | /studies/{study_uid}/study-disease-milestones              | <none>                                                                                          |
      | /studies/{study_uid}/study-disease-milestones/audit-trail  | <none>                                                                                          |
      | /studies/{study_uid}/study-disease-milestones/headers      | field_name=uid                                                                                  |
      | /studies/{study_uid}/study-element/audit-trail             | <none>                                                                                          |
      | /studies/{study_uid}/study-elements                        | <none>                                                                                          |
      | /studies/{study_uid}/study-elements/headers                | field_name=name                                                                                 |
      | /studies/{study_uid}/study-endpoints                       | <none>                                                                                          |
      | /studies/{study_uid}/study-endpoints/audit-trail           | <none>                                                                                          |
      | /studies/{study_uid}/study-endpoints/headers               | field_name=name                                                                                 |
      | /studies/{study_uid}/study-epochs/audit-trail              | <none>                                                                                          |
      | /studies/{study_uid}/study-epochs                          | <none>                                                                                          |
      | /studies/{study_uid}/study-epochs/headers                  | field_name=name                                                                                 |
      | /studies/{study_uid}/study-objectives                      | <none>                                                                                          |
      | /studies/{study_uid}/study-objectives.docx                 | <none>                                                                                          |
      | /studies/{study_uid}/study-objectives.html                 | <none>                                                                                          |
      | /studies/{study_uid}/study-objectives/audit-trail          | <none>                                                                                          |
      | /studies/{study_uid}/study-objectives/headers              | field_name=name                                                                                 |
      | /studies/{study_uid}/study-soa-footnote/audit-trail        | <none>                                                                                          |
      | /studies/{study_uid}/study-soa-footnotes                   | <none>                                                                                          |
      | /studies/{study_uid}/study-soa-footnotes/headers           | field_name=name                                                                                 |
      | /studies/{study_uid}/study-soa-groups                      | <none>                                                                                          |
      | /studies/{study_uid}/study-standard-versions               | <none>                                                                                          |
      | /studies/{study_uid}/study-standard-versions/audit-trail   | <none>                                                                                          |
      | /studies/{study_uid}/study-visits/audit-trail              | <none>                                                                                          |
      | /studies/{study_uid}/study-visits                          | <none>                                                                                          |
      | /studies/{study_uid}/study-visits-references               | <none>                                                                                          |
      | /studies/{study_uid}/study-visits/allowed-time-references  | <none>                                                                                          |
      | /studies/{study_uid}/study-visits/headers                  | field_name=name                                                                                 |
      | /studies/{study_uid}/time-units                            | <none>                                                                                          |
      | /studies/{study_uid}/complexity-score                      | <none>                                                                                          |
      | /study-activities                                          | <none>                                                                                          |
      | /study-activity-instances                                  | <none>                                                                                          |
      | /study-activity-instructions                               | <none>                                                                                          |
      | /study-arms                                                | <none>                                                                                          |
      | /study-compound-dosings/headers                            | field_name=name                                                                                 |
      | /study-compounds                                           | <none>                                                                                          |
      | /study-compounds/headers                                   | field_name=name                                                                                 |
      | /study-criteria                                            | <none>                                                                                          |
      | /study-criteria/headers                                    | field_name=name                                                                                 |
      | /study-elements/allowed-element-configs                    | <none>                                                                                          |
      | /study-endpoints                                           | <none>                                                                                          |
      | /study-endpoints/headers                                   | field_name=name                                                                                 |
      | /study-objectives                                          | <none>                                                                                          |
      | /study-objectives/headers                                  | field_name=name                                                                                 |
      | /study-soa-footnotes                                       | <none>                                                                                          |
      | /study-soa-footnotes/headers                               | field_name=name                                                                                 |
      | /template-parameters                                       | <none>                                                                                          |
      | /template-parameters/{name}/terms                          | <none>                                                                                          |
      | /timeframe-templates                                       | <none>                                                                                          |
      | /timeframe-templates/audit-trail                           | <none>                                                                                          |
      | /timeframe-templates/headers                               | field_name=name                                                                                 |
      | /timeframes                                                | <none>                                                                                          |
      | /timeframes/audit-trail                                    | <none>                                                                                          |
      | /timeframes/headers                                        | field_name=name                                                                                 |
      # | /studies/{study_uid}/global-anchor-visit                   | <none>                                                                                          |
      # | /standards/sponsor-models/dataset-classes                  | data_model_ig_name=SDTMIG, data_model_ig_version=3.2                                            |
      # | /standards/sponsor-models/dataset-classes/headers          | data_model_ig_name=SDTMIG, data_model_ig_version=3.2, field_name=label                          |
      # | /standards/sponsor-models/variable-classes                 | <none>                                                                                          |
      # | /standards/sponsor-models/variable-classes/headers         | field_name=label                                                                                |
      # | /listings/studies/study-metadata (requires a released study)                           | <none>                                                                                          |
      # | /studies/{study_uid}/copy-component                        | <none>                                                                                        |
      # | /listings/libraries/all/gcmd/cdisc-ct-val                  | <none>                                                                                        |
      # | /listings/libraries/all/gcmd/cdisc-ct-val/headers          | field_name=name                                                                               |
      # | /ct/catalogues/changes                                     | comparison_type=sponsor, start_datetime=<now>                                                 |

  @impact:api @impact:api_soa
  Scenario Outline: Endpoints for fetching SoA return with ok status for each study and its versions (latest/locked/released)
    Then the endpoint <url> called with query parameters <parameters> returns successfully for each study and its versions

    Examples:
      | url                                 | parameters                |
      | /studies/{study_uid}/flowchart      | layout=protocol           |
      | /studies/{study_uid}/flowchart      | layout=detailed           |
      | /studies/{study_uid}/flowchart      | layout=operational        |
      | /studies/{study_uid}/flowchart.html | layout=protocol           |
      | /studies/{study_uid}/flowchart.html | layout=protocol_lab_table |
      | /studies/{study_uid}/flowchart.html | layout=detailed           |
      | /studies/{study_uid}/flowchart.html | layout=operational        |
      | /studies/{study_uid}/flowchart.docx | layout=protocol           |
      | /studies/{study_uid}/flowchart.docx | layout=protocol_lab_table |
      | /studies/{study_uid}/flowchart.docx | layout=detailed           |
      | /studies/{study_uid}/flowchart.docx | layout=operational        |

  @impact:api @impact:api_soa
  Scenario Outline: Endpoints for fetching study cost complexity score return with ok status for each study and its versions (latest/locked/released)
    Then the endpoint <url> called with query parameters <parameters> returns successfully for each study and its versions

    Examples:
      | url                                   | parameters |
      | /studies/{study_uid}/complexity-score | <none>     |
