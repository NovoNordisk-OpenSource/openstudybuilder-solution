import datetime
from enum import Enum
from typing import Iterable

from neomodel import DoesNotExist, RelationshipManager, db

from clinical_mdr_api.domain_repositories.models.study import StudyRoot, StudyValue
from clinical_mdr_api.domain_repositories.models.study_audit_trail import (
    UpdateSoASnapshot,
)
from clinical_mdr_api.domain_repositories.models.study_selections import StudySelection
from clinical_mdr_api.domains.study_definition_aggregates.study_metadata import (
    StudyStatus,
)
from clinical_mdr_api.domains.study_selections.study_selection_base import (
    SOA_ITEM_TYPES,
    SoAItemType,
)
from clinical_mdr_api.models.study_selections.study_selection import (
    ReferencedItem,
    SoACellReference,
    SoAFootnoteReference,
)
from clinical_mdr_api.services._utils import ensure_transaction
from common.auth.user import user
from common.exceptions import NotFoundException
from common.telemetry import trace_calls

SOA_ITEM_TYPE_TO_RELATIONSHIP_MODEL_MAME_MAP = {
    SoAItemType.STUDY_EPOCH: "has_study_epoch",
    SoAItemType.STUDY_VISIT: "has_study_visit",
    SoAItemType.STUDY_SOA_GROUP: "has_study_soa_group",
    SoAItemType.STUDY_ACTIVITY_GROUP: "has_study_activity_group",
    SoAItemType.STUDY_ACTIVITY_SUBGROUP: "has_study_activity_subgroup",
    SoAItemType.STUDY_ACTIVITY: "has_study_activity",
    SoAItemType.STUDY_ACTIVITY_INSTANCE: "has_study_activity_instance",
    SoAItemType.STUDY_ACTIVITY_SCHEDULE: "has_study_activity_schedule",
    SoAItemType.STUDY_SOA_FOOTNOTE: "has_study_footnote",
}


class SoALayout(Enum):
    PROTOCOL = "protocol"
    DETAILED = "detailed"
    OPERATIONAL = "operational"


class StudySoARepository:
    @staticmethod
    def _study_value_query(
        study_uid: str, study_value_version: str | None
    ) -> tuple[str, dict[str:str]]:
        """constructs a Cypher query and params for getting the StudyValue node of a given study version

        Returns:
            str: the Cypher query
            dict[str: str]: query parameters
        """

        params = {
            "study_uid": study_uid,
        }

        if study_value_version:
            params["study_value_version"] = study_value_version
            params["study_status"] = StudyStatus.RELEASED.value
            query = [
                "MATCH (:StudyRoot {uid: $study_uid})-[:HAS_VERSION{status: $study_status, version: $study_value_version}]->(sv:StudyValue)"
            ]

        else:
            query = ["MATCH (:StudyRoot {uid: $study_uid})-[:LATEST]->(sv:StudyValue)"]

        return query, params

    @classmethod
    @trace_calls(args=[0, 1, 2], kwargs=["study_uid", "study_value_version", "layout"])
    def _disconnect_soa_rows(
        cls, study_uid: str, study_value_version: str, layout: SoALayout
    ):
        """Removes relationships HAS_PROTOCOL_SOA_CELL & HAS_PROTOCOL_SOA_FOOTNOTE of a given study version"""

        if layout != SoALayout.PROTOCOL:
            raise NotImplementedError("Only protocol SoA snapshot is implemented")

        sv_query, params = cls._study_value_query(study_uid, study_value_version)

        query = "\n".join(
            sv_query
            + [
                "MATCH (sv)-[cell:HAS_PROTOCOL_SOA_CELL]->(ss:StudySelection)",
                "DELETE cell",
            ]
        )
        db.cypher_query(query, params)

        query = "\n".join(
            sv_query
            + [
                "MATCH (sv)-[fn:HAS_PROTOCOL_SOA_FOOTNOTE]->(sfn:StudySoAFootnote)-[]->(ss)",
                "DELETE fn",
            ]
        )
        db.cypher_query(query, params)

    def load(
        self,
        study_uid: str,
        study_value_version: str | None = None,
        layout: SoALayout = SoALayout.PROTOCOL,
    ) -> tuple[list[SoACellReference], list[SoAFootnoteReference]]:
        """Loads SoA snapshot HAS_PROTOCOL_SOA_CELL & HAS_PROTOCOL_SOA_FOOTNOTE relationships of a given study version"""

        if layout != SoALayout.PROTOCOL:
            raise NotImplementedError("Only protocol SoA snapshot is implemented")

        sv_query, params = self._study_value_query(study_uid, study_value_version)

        query = list(sv_query)
        query.append("MATCH (sv)-[cell:HAS_PROTOCOL_SOA_CELL]->(ss:StudySelection)")
        query.append(
            "OPTIONAL MATCH (sv)-[fn:HAS_PROTOCOL_SOA_FOOTNOTE]->(sfn:StudySoAFootnote)-[]->(ss)"
        )
        query.append("WITH cell, ss, fn, sfn")
        query.append("ORDER BY cell.row, cell.column, cell.order, fn.order")
        query.append(
            "WITH cell, ss, COLLECT({order: fn.order, symbol: fn.symbol, uid: sfn.uid}) AS sfns"
        )
        query.append("RETURN cell, ss, sfns")

        query = "\n".join(query)
        results, _ = db.cypher_query(query, params)

        cell_references = [self._to_soa_cell_reference(*result) for result in results]

        query = list(sv_query)
        query.append(
            "MATCH (sv)-[fn:HAS_PROTOCOL_SOA_FOOTNOTE]->(sfn:StudySoAFootnote)"
        )
        query.append("RETURN fn, sfn")
        query.append("ORDER BY fn.order")

        query = "\n".join(query)
        results, _ = db.cypher_query(query, params)

        footnote_references = [
            self._to_soa_footnote_reference(*result) for result in results
        ]

        return cell_references, footnote_references

    @classmethod
    def _to_soa_cell_reference(cls, relationship, study_selection, footnotes):
        known_labels = study_selection.labels & SOA_ITEM_TYPES
        if not known_labels:
            raise RuntimeError(
                f"unknown SoAItemType: {', '.join(study_selection.labels)}"
            )
        label = next(iter(known_labels))

        return SoACellReference(
            row=relationship["row"],
            column=relationship["column"],
            span=relationship["span"],
            is_propagated=relationship["is_propagated"],
            order=relationship["order"],
            referenced_item=ReferencedItem(
                item_type=SoAItemType(label),
                item_uid=study_selection["uid"],
            ),
            footnote_references=[
                cls._to_soa_footnote_reference(footnote, footnote)
                for footnote in footnotes
                if footnote["uid"]
            ],
        )

    @staticmethod
    def _to_soa_footnote_reference(relationship, soa_footnote):
        return SoAFootnoteReference(
            order=relationship["order"],
            symbol=relationship["symbol"],
            referenced_item=ReferencedItem(
                item_type=SoAItemType.STUDY_SOA_FOOTNOTE,
                item_uid=soa_footnote["uid"],
            ),
        )

    @classmethod
    @trace_calls(
        args=[0, 3, 4, 5],
        kwargs=["study_uid", "study_value_version", "layout", "study_status"],
    )
    @ensure_transaction(db)
    def save(
        cls,
        study_uid: str,
        cell_references: list[SoACellReference],
        footnote_references: list[SoAFootnoteReference],
        study_value_version: str | None = None,
        layout: SoALayout = SoALayout.PROTOCOL,
        study_status: StudyStatus | None = None,
    ):
        """Saves SoA snapshot HAS_PROTOCOL_SOA_CELL & HAS_PROTOCOL_SOA_FOOTNOTE relationships of a given study version"""

        if layout != SoALayout.PROTOCOL:
            raise NotImplementedError("Only protocol SoA snapshot is implemented")

        try:
            study_root: StudyRoot = StudyRoot.nodes.get(uid=study_uid)
        except DoesNotExist as e:
            raise NotFoundException("Study", study_uid) from e

        if study_value_version:
            if study_status is None:
                study_status = StudyStatus.RELEASED

            try:
                study_value: StudyValue = study_root.has_version.match(
                    status=study_status.value, version=study_value_version
                )[0]
            except IndexError as e:
                raise NotFoundException(
                    msg=f"Study with specified uid '{study_uid}' and version '{study_value_version}' was not found."
                ) from e

        else:
            if study_status is None:
                study_status = StudyStatus.DRAFT

            study_value: StudyValue = study_root.latest_value.get()

        # delete previous SoA snapshot
        cls._disconnect_soa_rows(
            study_uid=study_uid, study_value_version=study_value_version, layout=layout
        )

        # save cells
        cls._save_relationship(
            relationship=study_value.has_protocol_soa_cell,
            references=cell_references,
            study_value=study_value,
        )

        # save footnotes
        cls._save_relationship(
            relationship=study_value.has_protocol_soa_footnote,
            references=footnote_references,
            study_value=study_value,
        )

        cls.manage_versioning_create(
            study_root=study_root,
            layout=layout,
            study_status=study_status,
        )

    @classmethod
    @trace_calls
    def _save_relationship(
        cls,
        relationship: RelationshipManager,
        references: Iterable[SoACellReference],
        study_value: StudyValue,
    ):
        for soa_cell_reference in references:
            referenced_item: ReferencedItem = soa_cell_reference.referenced_item

            try:
                relationship_property_name = (
                    SOA_ITEM_TYPE_TO_RELATIONSHIP_MODEL_MAME_MAP[
                        referenced_item.item_type
                    ]
                )
            except KeyError as exc:
                raise RuntimeError(
                    f"No domain model mapped for ReferencedItem type '{referenced_item.item_type}'"
                ) from exc

            try:
                ref_model: StudySelection = getattr(
                    study_value, relationship_property_name
                )
            except AttributeError as exc:
                raise RuntimeError(
                    f"Incorrect domain model mapped for ReferencedItem type '{referenced_item.item_type}', "
                    f"StudyValue has no '{relationship_property_name}'"
                ) from exc

            ref_node = ref_model.filter(uid=referenced_item.item_uid).first()

            ref_properties = {
                k: v
                for k, v in soa_cell_reference.model_dump().items()
                if k in {"row", "column", "span", "is_propagated", "order", "symbol"}
                and v is not None
            }

            relationship.connect(ref_node, ref_properties)

    @staticmethod
    def manage_versioning_create(
        study_root: StudyRoot,
        layout: SoALayout = SoALayout.PROTOCOL,
        study_status: StudyStatus = StudyStatus.DRAFT,
    ):
        action = UpdateSoASnapshot(
            date=datetime.datetime.now(datetime.timezone.utc),
            status=study_status.value,
            author_id=user().id(),
            object_type=f"{layout.value} SoA",
        )
        action.save()
        study_root.audit_trail.connect(action)
