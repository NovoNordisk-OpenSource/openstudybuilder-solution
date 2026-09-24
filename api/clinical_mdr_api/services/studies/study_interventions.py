"""Study Protocol Interventions service"""

import logging
from typing import Any, Mapping

from docx.enum.style import WD_STYLE_TYPE

from clinical_mdr_api.models.study_selections.study_selection import (
    StudyCompoundDosing,
    StudySelectionArm,
    StudySelectionCompound,
)
from clinical_mdr_api.services.studies.study_arm_selection import (
    StudyArmSelectionService,
)
from clinical_mdr_api.services.studies.study_compound_dosing_selection import (
    StudyCompoundDosingSelectionService,
)
from clinical_mdr_api.services.studies.study_compound_selection import (
    StudyCompoundSelectionService,
)
from clinical_mdr_api.services.utils.table_f import (
    TableCell,
    TableRow,
    TableWithFootnotes,
    table_to_docx,
    table_to_html,
)

# For future LOCALIZATION
_gettext = {
    "intervention_or_arm_name": "Intervention/Arm name",
    "intervention_name": "Intervention name",
    "intervention_type": "Intervention type",
    "investigational_or_non_investigational": "Investigational or non-investigational",
    "pharmaceutical_form": "Pharmaceutical form",
    "route_of_administration": "Route of administration",
    "medical_device": "Medical-device (if applicable)",
    "trial_product_strength": "Trial product strength",
    "dose_and_frequency": "Dose and dose frequency",
    "dosing_and_administration": "Dosing instructions and administration",
    "transfer_from_other_therapy": "Transfer from other therapy",
    "sourcing": "Sourcing",
    "packaging_and_labelling": "Packaging and labelling",
    "authorisation_status_in": "Authorisation status in",
    "medical_device_template": "Administered using {device} with a {dispensed_in}",
    "trial_product_strength_template": "{value} {unit}",
    "None": "None",
    "study_interventions": "Study Interventions",
    "no_information": "-",
}.get

log = logging.getLogger(__name__)

# pylint: disable=no-member
DOCX_STYLES = {
    "table": ("SB Table Condensed", WD_STYLE_TYPE.TABLE),
    "header1": ("Table Header lvl1", WD_STYLE_TYPE.PARAGRAPH),
    "header2": ("Table Header lvl2", WD_STYLE_TYPE.PARAGRAPH),
    None: ("Table Text", WD_STYLE_TYPE.PARAGRAPH),
}


class StudyInterventionsService:
    def get_table(self, study_uid: str) -> TableWithFootnotes:
        compounds = self._get_study_compounds(study_uid)
        arms = self._get_arms_for_compounds(study_uid)
        dosings = self._get_compound_dosings(study_uid)
        table = self.mk_table(compounds, arms, dosings)
        return table

    def get_html(self, study_uid: str) -> str:
        table = self.get_table(study_uid)
        return table_to_html(table)

    def get_docx(self, study_uid: str):
        table = self.get_table(study_uid)
        docx = table_to_docx(table, DOCX_STYLES)
        return docx

    @staticmethod
    # pylint: disable=unused-argument
    def mk_table(
        compounds: list[StudySelectionCompound],
        arms: Mapping[str, list[StudySelectionArm]],
        dosings: Mapping[str, list[StudyCompoundDosing]],
    ) -> TableWithFootnotes:
        table = TableWithFootnotes(
            num_header_rows=1,
            num_header_cols=1,
            title=_gettext("study_interventions"),
            id="StudyInterventionsTable",
        )

        table.rows.append(
            row := TableRow(
                cells=[
                    TableCell(
                        text=_gettext("intervention_or_arm_name"), style="header1"
                    )
                ]
            )
        )
        for cmp in compounds:
            row.cells.append(
                TableCell(
                    text=StudyInterventionsService._arm_txt(cmp, arms), style="header2"
                )
            )

        table.rows.append(
            row := TableRow(
                cells=[TableCell(text=_gettext("intervention_name"), style="header2")]
            )
        )
        for cmp in compounds:
            row.cells.append(
                TableCell(text=cmp.compound.name if cmp.compound.name else "")
            )

        table.rows.append(
            row := TableRow(
                cells=[TableCell(text=_gettext("intervention_type"), style="header2")]
            )
        )
        for cmp in compounds:
            row.cells.append(
                TableCell(
                    text=(
                        cmp.type_of_treatment.term_name if cmp.type_of_treatment else ""
                    )
                )
            )

        table.rows.append(
            row := TableRow(
                cells=[
                    TableCell(
                        text=_gettext("investigational_or_non_investigational"),
                        style="header2",
                    )
                ]
            )
        )
        for _ in compounds:
            row.cells.append(TableCell(text="?"))  # TODO

        # table.rows.append(
        #     row := TableRow(
        #         cells=[TableCell(text=_gettext("pharmaceutical_form"), style="header2")]
        #     )
        # )
        # for cmp in compounds:
        #     row.cells.append(
        #         TableCell(text=cmp.dosage_form.name if cmp.dosage_form else "")
        #     )

        # table.rows.append(
        #     row := TableRow(
        #         cells=[
        #             TableCell(text=_gettext("route_of_administration"), style="header2")
        #         ]
        #     )
        # )
        # for cmp in compounds:
        #     row.cells.append(
        #         TableCell(
        #             text=cmp.route_of_administration.name
        #             if cmp.route_of_administration
        #             else ""
        #         )
        #     )

        # table.rows.append(
        #     row := TableRow(
        #         cells=[TableCell(text=_gettext("medical_device"), style="header2")]
        #     )
        # )
        # for cmp in compounds:
        #     row.cells.append(cell := TableCell())
        #     mapping = {
        #         "device": cmp.delivery_device.name
        #         if cmp.delivery_device
        #         else _gettext("None"),
        #         "dispensed_in": (
        #             cmp.dispenser.name if cmp.dispenser else _gettext("None")
        #         ),
        #     }
        #     cell.text = _gettext("medical_device_template").format_map(mapping)

        # table.rows.append(
        #     row := TableRow(
        #         cells=[
        #             TableCell(text=_gettext("trial_product_strength"), style="header2")
        #         ]
        #     )
        # )
        # for cmp in compounds:
        #     row.cells.append(cell := TableCell())
        #     if cmp.strength_value:
        #         mapping = {
        #             "unit": cmp.strength_value.unit_label,
        #             "value": cmp.strength_value.value,
        #         }
        #         cell.text = _gettext("trial_product_strength_template").format_map(
        #             mapping
        #         )

        # table.rows.append(
        #     row := TableRow(
        #         cells=[TableCell(text=_gettext("dose_and_frequency"), style="header2")]
        #     )
        # )
        # for cmp in compounds:
        #     row.cells.append(
        #         TableCell(text=StudyInterventionsService._dosing_txt(cmp, dosings))
        #     )

        # table.rows.append(
        #     row := TableRow(
        #         cells=[
        #             TableCell(
        #                 text=_gettext("dosing_and_administration"), style="header2"
        #             )
        #         ]
        #     )
        # )
        # for cmp in compounds:
        #     row.cells.append(
        #         TableCell(text=cmp.other_info or _gettext("no_information"))
        #     )

        table.rows.append(
            row := TableRow(
                cells=[
                    TableCell(
                        text=_gettext("transfer_from_other_therapy"), style="header2"
                    )
                ]
            )
        )
        for _ in compounds:
            row.cells.append(TableCell(text="?"))  # TODO

        table.rows.append(
            row := TableRow(
                cells=[TableCell(text=_gettext("sourcing"), style="header2")]
            )
        )
        for _ in compounds:
            row.cells.append(TableCell(text="?"))  # TODO

        table.rows.append(
            row := TableRow(
                cells=[
                    TableCell(text=_gettext("packaging_and_labelling"), style="header2")
                ]
            )
        )
        for _ in compounds:
            row.cells.append(TableCell(text="?"))  # TODO

        table.rows.append(
            row := TableRow(
                cells=[
                    TableCell(text=_gettext("authorisation_status_in"), style="header2")
                ]
            )
        )
        for _ in compounds:
            row.cells.append(TableCell(text="?"))  # TODO

        return table

    @staticmethod
    def _dosing_txt(compounds, dosings):
        return "\n".join(
            f"{dosing.dose_value.value if dosing.dose_value else ''} "
            f"{dosing.dose_value.unit_label if dosing.dose_value else ''} "
            f"{dosing.dose_frequency.term_name if dosing.dose_frequency else ''}".strip()
            for dosing in dosings.get(compounds.study_compound_uid, [])
        ) or _gettext("no_information")

    @staticmethod
    def _arm_txt(compound, arms):
        return "\n".join(
            arm.name for arm in arms.get(compound.study_compound_uid, [])
        ) or _gettext("no_information")

    def _get_study_compounds(self, study_uid) -> list[StudySelectionCompound]:
        return (
            StudyCompoundSelectionService()
            .get_all_selection(
                study_uid=study_uid,
            )
            .items
        )

    def _get_arms_for_compounds(
        self, study_uid
    ) -> Mapping[str, list[StudySelectionArm]]:
        arms = {
            arm.arm_uid: arm
            for arm in StudyArmSelectionService()
            .get_all_selection(
                study_uid=study_uid,
            )
            .items
        }

        mapping = StudyCompoundSelectionService().get_compound_uid_to_arm_uids_mapping(
            study_uid
        )

        return {
            compound_uid: [arms[arm_uid] for arm_uid in arm_uids]
            for compound_uid, arm_uids in mapping.items()
        }

    def _get_compound_dosings(
        self, study_uid: str
    ) -> dict[str, list[StudyCompoundDosing]]:
        results = (
            StudyCompoundDosingSelectionService()
            .get_all_compound_dosings(study_uid)
            .items
        )

        mapping: dict[str, Any] = {}
        for dosing in results:
            key = dosing.study_compound.study_compound_uid
            mapping.setdefault(key, []).append(dosing)

        return mapping
