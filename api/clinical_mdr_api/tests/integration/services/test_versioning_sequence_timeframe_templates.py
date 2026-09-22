from typing import Any
from unittest import TestCase

from pydantic import BaseModel

import clinical_mdr_api.services.libraries.libraries as library_service
import clinical_mdr_api.services.syntax_templates.timeframe_templates as tt_service
from clinical_mdr_api.models.syntax_templates.timeframe_template import (
    TimeframeTemplate,
    TimeframeTemplateCreateInput,
    TimeframeTemplateEditInput,
)
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    library_data,
    template_data,
)
from common.exceptions import BusinessLogicException, NotFoundException


class TestCreate(TestCase):
    TEST_DB_NAME = "ttfversioning"
    timeframe_template: BaseModel

    @classmethod
    def setUp(cls):
        inject_and_clear_db(cls.TEST_DB_NAME)
        cls.library = library_service.create(**library_data)

    def test_create(self):
        data = {"name": template_data["name"], "library_name": self.library["name"]}
        timeframe_template = TimeframeTemplateCreateInput(**data)
        result = tt_service.TimeframeTemplateService().create(timeframe_template)
        self.assertIsInstance(result, TimeframeTemplate)
        self.assertEqual(result.name, template_data["name"])
        self.assertEqual(result.status, "Draft")
        self.assertEqual(result.version, "0.1")
        self.timeframe_template = result


# @pytest.mark.skip
class TestDraftEdit(TestCase):
    TEST_DB_NAME = "ttfversioning"

    @classmethod
    def setUp(cls):
        inject_and_clear_db(cls.TEST_DB_NAME)
        cls.library = library_service.create(**library_data)
        timeframe_template = TimeframeTemplateCreateInput(**template_data)
        cls.timeframe_template = tt_service.TimeframeTemplateService().create(
            timeframe_template
        )

    def test_edit(self):
        data: dict[Any, Any] = {
            "name": template_data["name"] + " edited",
            "change_description": "tested",
        }
        timeframe_template = TimeframeTemplateEditInput(**data)
        assert isinstance(self.timeframe_template, TimeframeTemplate)
        result = tt_service.TimeframeTemplateService().edit_draft(
            self.timeframe_template.uid, timeframe_template
        )
        assert isinstance(result, TimeframeTemplate)
        self.assertEqual(result.version, "0.2")
        self.assertEqual(result.status, "Draft")
        self.assertEqual(result.name, data["name"])

        data = {
            "name": template_data["name"] + " edited again",
            "change_description": "tested",
        }
        timeframe_template = TimeframeTemplateEditInput(**data)
        result = tt_service.TimeframeTemplateService().edit_draft(
            self.timeframe_template.uid, timeframe_template
        )
        assert isinstance(result, TimeframeTemplate)
        self.assertEqual(result.version, "0.3")
        self.assertEqual(result.status, "Draft")
        self.assertEqual(result.name, data["name"])


# @pytest.mark.skip
class TestApprove(TestCase):
    TEST_DB_NAME = "ttfversioning"

    @classmethod
    def setUp(cls):
        inject_and_clear_db(cls.TEST_DB_NAME)
        cls.library = library_service.create(**library_data)
        timeframe_template = TimeframeTemplateCreateInput(**template_data)
        timeframe_template = tt_service.TimeframeTemplateService().create(
            timeframe_template
        )
        assert isinstance(timeframe_template, TimeframeTemplate)
        cls.timeframe_template = timeframe_template

    def test_approve(self):
        result = tt_service.TimeframeTemplateService().approve(
            self.timeframe_template.uid
        )
        assert isinstance(result, TimeframeTemplate)
        self.assertEqual(result.version, "1.0")
        self.assertEqual(result.status, "Final")


class TestActivation(TestCase):
    TEST_DB_NAME = "ttfversioning"

    @classmethod
    def setUp(cls):
        inject_and_clear_db(cls.TEST_DB_NAME)
        cls.library = library_service.create(**library_data)
        timeframe_template = TimeframeTemplateCreateInput(**template_data)
        timeframe_template = tt_service.TimeframeTemplateService().create(
            timeframe_template
        )
        assert isinstance(timeframe_template, TimeframeTemplate)
        timeframe_template = tt_service.TimeframeTemplateService().approve(
            timeframe_template.uid
        )
        assert isinstance(timeframe_template, TimeframeTemplate)
        cls.timeframe_template = timeframe_template

    def test_activation(self):
        result = tt_service.TimeframeTemplateService().inactivate_final(
            self.timeframe_template.uid
        )
        assert isinstance(result, TimeframeTemplate)
        self.assertEqual(result.version, "1.0")
        self.assertEqual(result.status, "Retired")
        with self.assertRaises(BusinessLogicException):
            tt_service.TimeframeTemplateService().inactivate_final(
                self.timeframe_template.uid
            )

        result = tt_service.TimeframeTemplateService().reactivate_retired(
            self.timeframe_template.uid
        )
        assert isinstance(result, TimeframeTemplate)
        self.assertEqual(result.version, "1.0")
        self.assertEqual(result.status, "Final")
        with self.assertRaises(BusinessLogicException):
            tt_service.TimeframeTemplateService().reactivate_retired(
                self.timeframe_template.uid
            )


# @pytest.mark.skip
class TestSoftDelete(TestCase):
    TEST_DB_NAME = "ttfversioning"

    @classmethod
    def setUp(cls):
        inject_and_clear_db(cls.TEST_DB_NAME)
        cls.library = library_service.create(**library_data)
        timeframe_template = TimeframeTemplateCreateInput(**template_data)
        timeframe_template = tt_service.TimeframeTemplateService().create(
            timeframe_template
        )
        assert isinstance(timeframe_template, TimeframeTemplate)
        cls.timeframe_template = timeframe_template

    def test_softdelete(self):
        tt_service.TimeframeTemplateService().soft_delete(self.timeframe_template.uid)
        repos = MetaRepository()

        with self.assertRaises(NotFoundException) as message:
            repos.timeframe_template_repository.find_by_uid(self.timeframe_template.uid)
        self.assertEqual(
            "No TimeframeTemplateRoot with UID 'TimeframeTemplate_000001' found in given status, date and version.",
            message.exception.msg,
        )
