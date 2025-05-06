from unittest import TestCase

from pydantic import BaseModel

import clinical_mdr_api.services.libraries.libraries as library_service
import clinical_mdr_api.services.syntax_templates.objective_templates as service
from clinical_mdr_api.models.syntax_templates.objective_template import (
    ObjectiveTemplate,
    ObjectiveTemplateCreateInput,
    ObjectiveTemplateEditInput,
)
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    library_data,
    template_data,
)
from common.exceptions import BusinessLogicException, NotFoundException


class TestCreate(TestCase):
    TEST_DB_NAME = "utversioning"
    objective_template = None

    @classmethod
    def setUp(cls):
        inject_and_clear_db(cls.TEST_DB_NAME)
        cls.library = library_service.create(**library_data)

    def test_create(self):
        data = {"name": template_data["name"], "library_name": self.library["name"]}
        objective_template = ObjectiveTemplateCreateInput(**data)
        result = service.ObjectiveTemplateService().create(objective_template)
        self.assertIsInstance(result, ObjectiveTemplate)
        self.assertEqual(result.name, template_data["name"])
        self.assertEqual(result.status, "Draft")
        self.assertEqual(result.version, "0.1")
        self.objective_template = result.model_dump()


class TestDraftEdit(TestCase):
    TEST_DB_NAME = "utversioning"

    @classmethod
    def setUp(cls):
        inject_and_clear_db(cls.TEST_DB_NAME)
        cls.library = library_service.create(**library_data)
        objective_template = ObjectiveTemplateCreateInput(**template_data)
        cls.objective_template = service.ObjectiveTemplateService().create(
            objective_template
        )
        if isinstance(cls.objective_template, BaseModel):
            cls.objective_template = cls.objective_template.model_dump()

    def test_edit(self):
        data = {
            "name": template_data["name"] + " edited",
            "change_description": "tested",
        }
        objective_template = ObjectiveTemplateEditInput(**data)
        result = service.ObjectiveTemplateService().edit_draft(
            self.objective_template["uid"], objective_template
        )
        if isinstance(result, BaseModel):
            result = result.model_dump()
        self.assertEqual(result["version"], "0.2")
        self.assertEqual(result["status"], "Draft")
        self.assertEqual(result["name"], data["name"])

        data = {
            "name": template_data["name"] + " edited again",
            "change_description": "tested",
        }
        objective_template = ObjectiveTemplateEditInput(**data)
        result = service.ObjectiveTemplateService().edit_draft(
            self.objective_template["uid"], objective_template
        )
        if isinstance(result, BaseModel):
            result = result.model_dump()
        self.assertEqual(result["version"], "0.3")
        self.assertEqual(result["status"], "Draft")
        self.assertEqual(result["name"], data["name"])


class TestApprove(TestCase):
    TEST_DB_NAME = "utversioning"

    @classmethod
    def setUp(cls):
        inject_and_clear_db(cls.TEST_DB_NAME)
        cls.library = library_service.create(**library_data)
        objective_template = ObjectiveTemplateCreateInput(**template_data)
        cls.objective_template = service.ObjectiveTemplateService().create(
            objective_template
        )
        if isinstance(cls.objective_template, BaseModel):
            cls.objective_template = cls.objective_template.model_dump()

    def test_approve(self):
        result = service.ObjectiveTemplateService().approve(
            self.objective_template["uid"]
        )
        assert isinstance(result, ObjectiveTemplate)
        self.assertEqual(result.version, "1.0")
        self.assertEqual(result.status, "Final")


class TestActivation(TestCase):
    TEST_DB_NAME = "utversioning"

    @classmethod
    def setUp(cls):
        inject_and_clear_db(cls.TEST_DB_NAME)
        cls.library = library_service.create(**library_data)
        objective_template = ObjectiveTemplateCreateInput(**template_data)
        objective_template = service.ObjectiveTemplateService().create(
            objective_template
        )
        cls.objective_template = service.ObjectiveTemplateService().approve(
            objective_template.uid
        )
        if isinstance(cls.objective_template, BaseModel):
            cls.objective_template = cls.objective_template.model_dump()

    def test_activation(self):
        result = service.ObjectiveTemplateService().inactivate_final(
            self.objective_template["uid"]
        )
        assert isinstance(result, ObjectiveTemplate)
        self.assertEqual(result.version, "1.0")
        self.assertEqual(result.status, "Retired")
        with self.assertRaises(BusinessLogicException):
            service.ObjectiveTemplateService().inactivate_final(
                self.objective_template["uid"]
            )

        result = service.ObjectiveTemplateService().reactivate_retired(
            self.objective_template["uid"]
        )
        assert isinstance(result, ObjectiveTemplate)
        self.assertEqual(result.version, "1.0")
        self.assertEqual(result.status, "Final")
        with self.assertRaises(BusinessLogicException):
            service.ObjectiveTemplateService().reactivate_retired(
                self.objective_template["uid"]
            )


class TestSoftDelete(TestCase):
    TEST_DB_NAME = "utversioning"

    @classmethod
    def setUp(cls):
        inject_and_clear_db(cls.TEST_DB_NAME)
        cls.library = library_service.create(**library_data)
        objective_template = ObjectiveTemplateCreateInput(**template_data)
        cls.objective_template = service.ObjectiveTemplateService().create(
            objective_template
        )
        if isinstance(cls.objective_template, BaseModel):
            cls.objective_template = cls.objective_template.model_dump()

    def test_softdelete(self):
        service.ObjectiveTemplateService().soft_delete(self.objective_template["uid"])
        repos = MetaRepository()

        with self.assertRaises(NotFoundException) as message:
            repos.objective_template_repository.find_by_uid(
                self.objective_template["uid"]
            )
        self.assertEqual(
            "No ObjectiveTemplateRoot with UID 'ObjectiveTemplate_000001' found in given status, date and version.",
            message.exception.msg,
        )
