from clinical_mdr_api.domain_repositories.models.standard_data_model import (
    DataModelRoot,
    DataModelValue,
)
from clinical_mdr_api.domain_repositories.standard_data_models.standard_data_model_repository import (
    StandardDataModelRepository,
)
from clinical_mdr_api.models.standard_data_models.data_model import DataModel


class DataModelRepository(StandardDataModelRepository):
    root_class = DataModelRoot
    value_class = DataModelValue
    return_model = DataModel

    def specific_alias_clause(self) -> str:
        return """
        DISTINCT *
            CALL (standard_root, standard_value) {
                MATCH (standard_root)-[hv:HAS_VERSION]-(standard_value)
                WITH hv
                ORDER BY
                    toInteger(split(hv.version, '.')[0]) ASC,
                    toInteger(split(hv.version, '.')[1]) ASC,
                    hv.end_date ASC,
                    hv.start_date ASC
                WITH collect(hv) as hvs
                RETURN last(hvs) AS version_rel
            }
        WITH *,
            standard_root.uid AS uid,
            standard_value.name AS name,
            standard_value.description AS description,
            version_rel.start_date AS start_date,
            version_rel.end_date AS end_date,
            version_rel.status AS status,
            standard_value.version_number AS version_number,
            [(standard_value)<-[:IMPLEMENTS]-(implementation_guide_value:DataModelIGValue)<-[:HAS_VERSION]-
            (implementation_guide_root:DataModelIGRoot) | 
                {uid:implementation_guide_root.uid, name:implementation_guide_value.name}] AS implementation_guides
        """

    def sort_by(self) -> dict[str, bool] | None:
        return {"version_number": False}
