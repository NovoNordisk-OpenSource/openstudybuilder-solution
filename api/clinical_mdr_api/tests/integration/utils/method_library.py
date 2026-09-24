from clinical_mdr_api.domain_repositories.models.study import StudyRoot
from clinical_mdr_api.services.libraries import libraries as library_service
from clinical_mdr_api.tests.integration.utils.data_library import library_data

# pylint: disable=unused-wildcard-import,wildcard-import
from clinical_mdr_api.tests.integration.utils.factory_activity import *
from clinical_mdr_api.tests.integration.utils.factory_controlled_terminology import *
from clinical_mdr_api.tests.integration.utils.factory_disease_milestone import *
from clinical_mdr_api.tests.integration.utils.factory_epoch import *
from clinical_mdr_api.tests.integration.utils.factory_metadata import *
from clinical_mdr_api.tests.integration.utils.factory_study_design import *
from clinical_mdr_api.tests.integration.utils.factory_units import *
from clinical_mdr_api.tests.integration.utils.factory_visit import *


def generate_study_root():
    StudyRoot.generate_node_uids_if_not_present()
    study = StudyRoot.nodes.all()[0]
    return study


def create_library_data():
    library_service.create(**library_data)  # type: ignore[arg-type]
