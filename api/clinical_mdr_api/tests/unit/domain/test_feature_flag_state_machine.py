import unittest

from clinical_mdr_api.domains.feature_flags.state_machine import FeatureFlagStateMachine
from common.exceptions import BusinessLogicException


class TestFeatureFlagStateMachine(unittest.TestCase):
    def test_update_allowed_for_final(self):
        FeatureFlagStateMachine.ensure_can_update("Final")

    def test_update_rejected_for_retired(self):
        with self.assertRaises(BusinessLogicException):
            FeatureFlagStateMachine.ensure_can_update("Retired")

    def test_inactivate_allowed_for_final(self):
        FeatureFlagStateMachine.ensure_can_inactivate("Final")

    def test_inactivate_rejected_for_retired(self):
        with self.assertRaises(BusinessLogicException):
            FeatureFlagStateMachine.ensure_can_inactivate("Retired")

    def test_reactivate_allowed_for_retired(self):
        FeatureFlagStateMachine.ensure_can_reactivate("Retired")

    def test_reactivate_rejected_for_final(self):
        with self.assertRaises(BusinessLogicException):
            FeatureFlagStateMachine.ensure_can_reactivate("Final")
