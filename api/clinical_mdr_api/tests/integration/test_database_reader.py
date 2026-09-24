import unittest

from clinical_mdr_api.domains.study_definition_aggregates.study_configuration import (
    _STATIC_FIELD_CONFIG,
    FieldConfiguration,
)


class TestConfigurationReaders(unittest.TestCase):
    def test__static_config__is_populated(self):
        config = FieldConfiguration.default_field_config()
        self.assertTrue(len(config) > 0)
        self.assertEqual(config, _STATIC_FIELD_CONFIG)
