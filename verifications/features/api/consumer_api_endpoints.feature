Feature: All API endpoints can be called successfully

  Background:
    Given the database is reachable and has content
    And the API is reachable

  @impact:consumer_api
  Scenario Outline: Endpoints that take a series of parameters return with ok status
    Then consumer api endpoint <url> called with a list of <parameters> returns successfully

    Examples:
      | url                                              | parameters                                                                                                   |
      | /v1/studies                                      | <none>                                                                                                       |
      | /v1/studies                                      | id=1, sort_by=id_prefix, sort_order=asc, page_size=100, page_number=1                                        |
      | /v1/studies                                      | sort_by=number, sort_order=desc, page_size=100, page_number=1                                                |
      | /v1/studies/{study_uid}/study-visits             | <none>                                                                                                       |
      | /v1/studies/{study_uid}/study-visits             | sort_by=uid, sort_order=asc, page_size=100, page_number=1                                                    |
      | /v1/studies/{study_uid}/study-visits             | sort_by=visit_name, sort_order=asc, page_size=100, page_number=1                                             |
      | /v1/studies/{study_uid}/study-visits             | sort_by=unique_visit_number, sort_order=desc, page_size=100, page_number=1                                   |
      | /v1/studies/{study_uid}/study-activities         | <none>                                                                                                       |
      | /v1/studies/{study_uid}/study-activities         | sort_by=activity_name, sort_order=asc, page_size=100, page_number=1                                          |
      | /v1/studies/{study_uid}/study-activities         | sort_by=uid, sort_order=desc, page_size=100, page_number=1                                                   |
      | /v1/studies/{study_uid}/study-activity-instances | <none>                                                                                                       |
      | /v1/studies/{study_uid}/study-activity-instances | sort_by=activity.name, sort_order=asc, page_size=100, page_number=1                                          |
      | /v1/studies/{study_uid}/study-activity-instances | sort_by=activity_instance.name, sort_order=desc, page_size=50, page_number=1                                 |
      | /v1/studies/{study_uid}/study-activity-instances | sort_by=uid, sort_order=desc, page_size=100, page_number=1                                                   |
      | /v1/studies/{study_uid}/detailed-soa             | <none>                                                                                                       |
      | /v1/studies/{study_uid}/detailed-soa             | sort_by=activity_name, sort_order=asc, page_size=100, page_number=1                                          |
      | /v1/studies/{study_uid}/detailed-soa             | sort_by=visit_short_name, sort_order=desc, page_size=100, page_number=1                                      |
      | /v1/studies/{study_uid}/detailed-soa             | sort_by=epoch_name, sort_order=desc, page_size=100, page_number=1                                            |
      | /v1/studies/{study_uid}/detailed-soa             | sort_by=activity_group_name, sort_order=desc, page_size=100, page_number=1                                   |
      | /v1/studies/{study_uid}/detailed-soa             | sort_by=activity_group_name, sort_order=asc, page_size=100, page_number=1                                    |
      | /v1/studies/{study_uid}/detailed-soa             | sort_by=activity_subgroup_name, sort_order=desc, page_size=100, page_number=1                                |
      | /v1/studies/{study_uid}/detailed-soa             | sort_by=soa_group_name, sort_order=desc, page_size=100, page_number=1                                        |
      | /v1/studies/{study_uid}/operational-soa          | <none>                                                                                                       |
      | /v1/studies/{study_uid}/operational-soa          | sort_by=activity_name, sort_order=asc, page_size=100, page_number=1                                          |
      | /v1/studies/{study_uid}/operational-soa          | sort_by=activity_name, sort_order=desc, page_size=100, page_number=1                                         |
      | /v1/studies/{study_uid}/operational-soa          | sort_by=activity_name, sort_order=asc, page_size=100, page_number=1                                          |
      | /v1/studies/{study_uid}/operational-soa          | sort_by=visit_uid, sort_order=desc, page_size=100, page_number=1                                             |
      | /v1/studies/audit-trail                          | from_ts=2024-01-01T00:00:00Z, to_ts=2030-01-01T00:00:00Z                                                     |
      | /v1/library/activities                           | sort_by=name, sort_order=desc, page_size=100, page_number=1                                                  |
      | /v1/library/activities                           | library=Sponsor, status=Final, page_size=100, page_number=1                                                  |
      | /v1/library/activity-instances                   | sort_by=name, sort_order=desc, page_size=100, page_number=1                                                  |
      | /v1/library/activity-instances                   | library=Sponsor, status=Final, page_size=100, page_number=1                                                  |
      | /v1/library/activity-instances                   | library=Requested, activity_uid=xyz, page_size=100, page_number=1                                            |
      | /v1/library/ct/codelists                         | name_status=Draft, attributes_status=Draft, page_size=100, page_number=1                                     |
      | /v1/library/ct/codelists                         | <none>                                                                                                       |
      | /v1/library/ct/codelist-terms                    | codelist_submission_value=EPOCHSTP, name_status=Draft, attributes_status=Draft, page_size=100, page_number=1 |
      | /v1/library/ct/codelist-terms                    | codelist_submission_value=TIMELB                                                                             |
      | /v1/library/unit-definitions                     | subset=Study Time, name_status=Draft, attributes_status=Draft, page_size=100, page_number=1                  |
      | /v1/library/unit-definitions                     | <none>                                                                                                       |
