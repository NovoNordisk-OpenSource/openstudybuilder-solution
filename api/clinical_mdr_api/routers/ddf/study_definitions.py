import re
from pathlib import Path as PathFromPathLib
from typing import Annotated, Any

from fastapi import APIRouter, Path, Request
from fastapi.templating import Jinja2Templates

from clinical_mdr_api.domain_repositories.study_selections.study_soa_repository import (
    SoALayout,
)
from clinical_mdr_api.models.utils import PrettyJSONResponse
from clinical_mdr_api.routers import _generic_descriptions
from clinical_mdr_api.services.ddf.usdm_service import USDMService
from clinical_mdr_api.services.studies.study_design_figure import (
    StudyDesignFigureService,
)
from clinical_mdr_api.services.studies.study_flowchart import StudyFlowchartService
from common.auth import rbac
from common.auth.dependencies import security
from common.models.error import ErrorResponse
from common.telemetry import trace_block

router = APIRouter(prefix="/studyDefinitions")

M11_TEMPLATES_DIR_PATH = (
    PathFromPathLib(__file__).parent.parent.parent.parent / "m11-templates"
)
templates = Jinja2Templates(directory=str(M11_TEMPLATES_DIR_PATH))


@router.get(
    path="/{study_uid}",
    dependencies=[security, rbac.STUDY_READ],
    response_class=PrettyJSONResponse,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The study with the specified 'study_uid' wasn't found.",
        },
    },
    summary="""Return an entire study in DDF USDM format""",
    description="""
State before:
- Study must exist.

State after:
- no change.

Possible errors:
- Invalid study-uid.
""",
)
def get_study(
    study_uid: Annotated[str, Path(description="The unique uid of the study.")],
) -> dict[str, Any]:
    usdm_service = USDMService()
    ddf_study_wrapper = usdm_service.get_by_uid(study_uid)
    return ddf_study_wrapper


@router.get(
    path="/{study_uid}/m11",
    dependencies=[security, rbac.STUDY_READ],
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"content": {"text/html": {"schema": {"type": "string"}}}},
        404: _generic_descriptions.ERROR_404,
    },
    summary="""Return an HTML representation of the ICH M11 protocol of the study with the specified 'study_uid'.""",
    description="""
State before:
- Study must exist.

State after:
- no change.

Possible errors:
- Invalid study-uid.
""",
)
def get_study_m11_protocol(
    request: Request,
    study_uid: Annotated[str, Path(description="The unique uid of the study.")],
):
    usdm_service = USDMService()
    ddf_study_wrapper = usdm_service.get_by_uid(study_uid)
    ddf_study = ddf_study_wrapper.get("study")

    study_flowchart = StudyFlowchartService().get_study_flowchart_html(
        study_uid=study_uid,
        study_value_version=None,
        layout=SoALayout.DETAILED,
    )
    study_flowchart_html_table_str = re.search(
        "<table>(.|\n)*?</table>", study_flowchart
    ).group(0)

    study_design_figure = StudyDesignFigureService(debug=False).get_svg_document(
        study_uid, study_value_version=None
    )

    with open(
        str(M11_TEMPLATES_DIR_PATH)
        + "/ICH_Step4_M11_Final_TechnicalSpecification_2025_1119.json",
        "r",
        encoding="utf-8",
    ) as f:
        specification = f.read()

    with trace_block("context_creation", "Creating context for M11 template rendering"):
        context = {
            "specification_20251119": specification,
            "study_id": study_uid,
            "study_indications": ddf_study.versions[0].studyDesigns[0].indications,
            "study_interventions": ddf_study.versions[0].studyInterventions[0],
            "study_name": ddf_study.name,
            "protocol_full_title": ddf_study.description,
            "study_design_figure_svg": study_design_figure,
            "study_flowchart_html_table": study_flowchart_html_table_str,
            "protocol_short_title": ddf_study.label,
            "protocol_acronym": study_uid,
            #        "sponsor_name": ddf_study.versions[0].studyIdentifiers[0].scopeId,
            "sponsor_legal_address": "Novo Nordisk A/S Novo Allé, 2880 Bagsvaerd Denmark Tel: +45 4444 8888",
            #        "protocol_number": ddf_study.versions[0].studyIdentifiers[0].id,
            "protocol_version": ddf_study.documentedBy[0].versions[0].version,
            "trial_phase": (
                ddf_study.versions[0].studyDesigns[0].studyPhase.standardCode
            ),
            "primary_objectives": [
                objective.dict()
                for objective in ddf_study.versions[0].studyDesigns[0].objectives
                if "primary" in objective.level.decode.lower()
            ],
            "secondary_objectives": [
                objective.dict()
                for objective in ddf_study.versions[0].studyDesigns[0].objectives
                if "secondary" in objective.level.decode.lower()
            ],
            # TODO: reactivate when intervention model is available in package as InterventionalStudyDesign attribute
            # "intervention_model": ddf_study.versions[0]
            # .studyDesigns[0]
            # .interventionModel.decode
            # or "",
            "population_healthy_subjects": ddf_study.versions[0]
            .studyDesigns[0]
            .population.includesHealthySubjects,
            "population_planned_maximum_age": (
                (
                    ddf_study.versions[0]
                    .studyDesigns[0]
                    .population.plannedAge.maxValue.value
                )
                if (
                    ddf_study.versions[0].studyDesigns[0].population.plannedAge
                    is not None
                )
                else "Missing"
            ),
            "population_planned_maximum_age_unit": (
                (
                    ddf_study.versions[0]
                    .studyDesigns[0]
                    .population.plannedAge.maxValue.unit.standardCode.decode
                )
                if (
                    ddf_study.versions[0].studyDesigns[0].population.plannedAge
                    is not None
                )
                else "Missing"
            ),
            "population_planned_minimum_age": (
                (
                    ddf_study.versions[0]
                    .studyDesigns[0]
                    .population.plannedAge.minValue.value
                )
                if (
                    ddf_study.versions[0].studyDesigns[0].population.plannedAge
                    is not None
                )
                else "Missing"
            ),
            "population_planned_minimum_age_unit": (
                (
                    ddf_study.versions[0]
                    .studyDesigns[0]
                    .population.plannedAge.minValue.unit.standardCode.decode
                )
                if (
                    ddf_study.versions[0].studyDesigns[0].population.plannedAge
                    is not None
                )
                else "Missing"
            ),
            "population_planned_enrollment_number_quantity_value": (
                int(
                    ddf_study.versions[0]
                    .studyDesigns[0]
                    .population.plannedEnrollmentNumber.value
                )
                if (
                    ddf_study.versions[0]
                    .studyDesigns[0]
                    .population.plannedEnrollmentNumber
                )
                is not None
                else "Missing"
            ),
            "trial_intervention_total_duration": (
                ddf_study.versions[0]
                .studyDesigns[0]
                .scheduleTimelines[0]
                .timings[-1]
                .valueLabel
                if len(
                    ddf_study.versions[0].studyDesigns[0].scheduleTimelines[0].timings
                )
                > 0
                else None
            ),
            "number_of_arms": len(ddf_study.versions[0].studyDesigns[0].arms),
            "civ_id_sin_number": next(
                (
                    identifier.text
                    for identifier in ddf_study.versions[0].studyIdentifiers
                    if identifier.scopeId == "civ_id_sin_number"
                ),
                None,
            ),
            "ct_gov_id": next(
                (
                    identifier.text
                    for identifier in ddf_study.versions[0].studyIdentifiers
                    if identifier.scopeId == "ct_gov_id"
                ),
                None,
            ),
            "eudamed_srn_number": next(
                (
                    identifier.text
                    for identifier in ddf_study.versions[0].studyIdentifiers
                    if identifier.scopeId == "eudamed_srn_number"
                ),
                None,
            ),
            "eudract_id": next(
                (
                    identifier.text
                    for identifier in ddf_study.versions[0].studyIdentifiers
                    if identifier.scopeId == "eudract_id"
                ),
                None,
            ),
            "eu_trial_number": next(
                (
                    identifier.text
                    for identifier in ddf_study.versions[0].studyIdentifiers
                    if identifier.scopeId == "eu_trial_number"
                ),
                None,
            ),
            "investigational_device_exemption_ide_number": next(
                (
                    identifier.text
                    for identifier in ddf_study.versions[0].studyIdentifiers
                    if (
                        identifier.scopeId
                        == "investigational_device_exemption_ide_number"
                    )
                ),
                None,
            ),
            "investigational_new_drug_application_number_ind": next(
                (
                    identifier.text
                    for identifier in ddf_study.versions[0].studyIdentifiers
                    if (
                        identifier.scopeId
                        == "investigational_new_drug_application_number_ind"
                    )
                ),
                None,
            ),
            "japanese_trial_registry_id_japic": next(
                (
                    identifier.text
                    for identifier in ddf_study.versions[0].studyIdentifiers
                    if identifier.scopeId == "japanese_trial_registry_id_japic"
                ),
                None,
            ),
            "japanese_trial_registry_number_jrct": next(
                (
                    identifier.text
                    for identifier in ddf_study.versions[0].studyIdentifiers
                    if identifier.scopeId == "japanese_trial_registry_number_jrct"
                ),
                None,
            ),
            "national_clinical_trial_number": next(
                (
                    identifier.text
                    for identifier in ddf_study.versions[0].studyIdentifiers
                    if identifier.scopeId == "national_clinical_trial_number"
                ),
                None,
            ),
            "national_medical_products_administration_nmpa_number": next(
                (
                    identifier.text
                    for identifier in ddf_study.versions[0].studyIdentifiers
                    if (
                        identifier.scopeId
                        == "national_medical_products_administration_nmpa_number"
                    )
                ),
                None,
            ),
            "universal_trial_number_utn": next(
                (
                    identifier.text
                    for identifier in ddf_study.versions[0].studyIdentifiers
                    if identifier.scopeId == "universal_trial_number_utn"
                ),
                None,
            ),
            "eu_pas_number": next(
                (
                    identifier.text
                    for identifier in ddf_study.versions[0].studyIdentifiers
                    if identifier.scopeId == "eu_pas_number"
                ),
                None,
            ),
        }

    with trace_block("template_rendering", "Rendering M11 template"):
        template_response = templates.TemplateResponse(
            request=request, name="m11-template.html", context=context
        )
    return template_response
