import unittest

from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import inject_base_data
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from common.exceptions import NotFoundException


class TestStudyBranchArmCohortNotFound(unittest.TestCase):
    def setUp(self):
        inject_and_clear_db("brancharmselectiontest")
        study, _ = inject_base_data()
        self.study_uid = study.uid
        arm = TestUtils.create_study_arm(
            study_uid=self.study_uid,
            name="Arm A",
            short_name="A",
        )
        self.arm_uid = arm.arm_uid

    def test_nonexistent_cohort_uid_raises_not_found(self):
        # A study_cohort_uid that resolves to no graph node previously raised
        # a neomodel StudyCohortDoesNotExist (500); after the fix it must raise
        # NotFoundException (404).
        with self.assertRaises(NotFoundException):
            TestUtils.create_study_branch_arm(
                study_uid=self.study_uid,
                name="Branch Arm A",
                short_name="BA",
                study_arm_uid=self.arm_uid,
                study_cohort_uid="nonexistent_cohort_uid",
            )
