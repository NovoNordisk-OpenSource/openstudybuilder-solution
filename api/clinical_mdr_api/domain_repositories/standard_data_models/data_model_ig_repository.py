from clinical_mdr_api.domain_repositories.models.standard_data_model import (
    DataModelIGRoot,
    DataModelIGValue,
)
from clinical_mdr_api.domain_repositories.standard_data_models.standard_data_model_repository import (
    StandardDataModelRepository,
)
from clinical_mdr_api.models.standard_data_models.data_model_ig import DataModelIG


class DataModelIGRepository(StandardDataModelRepository):
    root_class = DataModelIGRoot
    value_class = DataModelIGValue
    return_model = DataModelIG

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
            standard_value.version_number AS version_number,
            version_rel.start_date AS start_date,
            version_rel.end_date AS end_date,
            version_rel.status AS status,
            head([(standard_value)-[:IMPLEMENTS]->(implemented_data_model_value:DataModelValue)<-[:HAS_VERSION]-
            (implemented_data_model_root:DataModelRoot) | 
                {uid:implemented_data_model_root.uid, name:implemented_data_model_value.name}]) AS implemented_data_model
        """

    def sort_by(self) -> dict[str, bool] | None:
        return {"version_number": False}
