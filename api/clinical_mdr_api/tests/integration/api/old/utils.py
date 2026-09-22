def assert_study_arm(res, test_data_arm):
    print("--- assert_study_arm")
    print("res")
    print(res)
    print("test_data_arm")
    print(test_data_arm)
    assert res["study_uid"] == test_data_arm.study_uid
    assert res["arm_uid"] == test_data_arm.arm_uid
    # assert res["order"] == test_data_arm.order
    assert res["name"] == test_data_arm.name
    assert res["short_name"] == test_data_arm.short_name
    assert res["code"] == test_data_arm.code
    # assert res["start_date"] == test_data_dict["arm3"].start_date
    assert res["end_date"] == test_data_arm.end_date
    assert res["status"] == test_data_arm.status
    assert res["change_type"] == test_data_arm.change_type
    assert res["accepted_version"] == test_data_arm.accepted_version
    assert res["arm_type"]["term_uid"] == test_data_arm.arm_type.term_uid
    assert res["arm_type"]["term_name"] == test_data_arm.arm_type.term_name
    assert res["arm_type"]["codelist_uid"] == test_data_arm.arm_type.codelist_uid
    assert res["arm_type"]["codelist_name"] == test_data_arm.arm_type.codelist_name
    assert (
        res["arm_type"]["codelist_submission_value"]
        == test_data_arm.arm_type.codelist_submission_value
    )
    assert res["arm_type"]["order"] == test_data_arm.arm_type.order
    assert (
        res["arm_type"]["submission_value"] == test_data_arm.arm_type.submission_value
    )
    # assert res["arm_type"]["queried_effective_date"] is not None
    assert res["arm_type"]["date_conflict"] is False
    assert res["description"] == test_data_arm.description
    assert res["number_of_subjects"] == test_data_arm.number_of_subjects
    assert res["randomization_group"] == test_data_arm.randomization_group
    assert res["author_username"] == test_data_arm.author_username
