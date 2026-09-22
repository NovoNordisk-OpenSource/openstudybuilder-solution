from neomodel import db

from common.exceptions import NotFoundException


class MetadataRepository:
    CSV_EXPORT_QUERY = """
    CALL apoc.export.csv.query(query, null, {stream:true, params:{target_uid: $target_uid}})
    YIELD data, rows
    RETURN data, rows;"""

    OPTIONAL_FORM_MATCH = """
    OPTIONAL MATCH (OdmStudyEventValue)
    -[:FORM_REF]->(OdmFormValue:OdmFormValue)
    <-[:LATEST_FINAL|LATEST_RETIRED]-(OdmFormRoot:OdmFormRoot)
    CALL (OdmFormRoot, OdmFormValue) {
        MATCH (OdmFormRoot)-[hv:HAS_VERSION]->(OdmFormValue)
        WHERE hv.status in ['Final', 'Retired'] 
        WITH hv
        ORDER BY
            toInteger(split(hv.version, '.')[0]) ASC,
            toInteger(split(hv.version, '.')[1]) ASC,
            hv.end_date ASC,
            hv.start_date ASC
        WITH collect(hv) as hvs
        RETURN last(hvs) as OdmFormLatest
    }
    """
    OPTIONAL_ITEM_GROUP_MATCH = """
    OPTIONAL MATCH (OdmFormValue)
    -[:ITEM_GROUP_REF]->(OdmItemGroupValue:OdmItemGroupValue)
    <-[:LATEST_FINAL|LATEST_RETIRED]-(OdmItemGroupRoot:OdmItemGroupRoot)
    CALL (OdmItemGroupRoot, OdmItemGroupValue) {
        MATCH (OdmItemGroupRoot)-[hv:HAS_VERSION]->(OdmItemGroupValue)
        WHERE hv.status in ['Final', 'Retired'] 
        WITH hv
        ORDER BY
            toInteger(split(hv.version, '.')[0]) ASC,
            toInteger(split(hv.version, '.')[1]) ASC,
            hv.end_date ASC,
            hv.start_date ASC
        WITH collect(hv) as hvs
        RETURN last(hvs) as OdmItemGroupLatest
    }
    """
    OPTIONAL_ITEM_MATCH = """
    OPTIONAL MATCH (OdmItemGroupValue)
    -[:ITEM_REF]->(OdmItemValue:OdmItemValue)
    <-[:LATEST_FINAL|LATEST_RETIRED]-(OdmItemRoot:OdmItemRoot)
    CALL (OdmItemRoot, OdmItemValue) {
        MATCH (OdmItemRoot)-[hv:HAS_VERSION]->(OdmItemValue)
        WHERE hv.status in ['Final', 'Retired']
        WITH hv
        ORDER BY
            toInteger(split(hv.version, '.')[0]) ASC,
            toInteger(split(hv.version, '.')[1]) ASC,
            hv.end_date ASC,
            hv.start_date ASC
        WITH collect(hv) as hvs
        RETURN last(hvs) as OdmItemLatest
    }
    """
    OPTIONAL_UNIT_DEFINITION_MATCH = """
    OPTIONAL MATCH (OdmItemValue)
    -[:HAS_UNIT_DEFINITION]->(UnitDefinitionRoot:UnitDefinitionRoot)
    -[:LATEST]->(UnitDefinitionValue:UnitDefinitionValue)
    """
    OPTIONAL_CODELIST_MATCH = """
    OPTIONAL MATCH (OdmItemValue)
    -[:HAS_CODELIST]->(CTCodelistRoot:CTCodelistRoot)
    -[:HAS_ATTRIBUTES_ROOT]->(CTCodelistAttributesRoot:CTCodelistAttributesRoot)
    -[:LATEST]->(CTCodelistAttributesValue:CTCodelistAttributesValue)
    """
    OPTIONAL_CODELIST_TERM_MATCH = """
    OPTIONAL MATCH (OdmItemValue)
    -[:HAS_CODELIST_TERM]->(:CTTermContext)
    -[:HAS_SELECTED_CODELIST]-(:CTCodelistRoot)
    -[:HAS_TERM]-(CTCodelistTerm:CTCodelistTerm)
    """
    OPTIONAL_DATATYPE_MATCH = """
    OPTIONAL MATCH (OdmItemValue)-[:HAS_DATA_TYPE]->(DataTypeContext:CTTermContext)
    -[:HAS_SELECTED_CODELIST]->(:CTCodelistRoot)
    -[:HAS_TERM]->(DataTypeCTCodelistTerm:CTCodelistTerm)
    -[:HAS_TERM_ROOT]->(:CTTermRoot)<-[:HAS_SELECTED_TERM]-(DataTypeContext)
    """

    STUDY_EVENT_NAME_RETURN = "OdmStudyEventValue.name AS StudyEvent_Name"
    STUDY_EVENT_VERSION_RETURN = "OdmStudyEventLatest.version AS StudyEvent_Version"
    FORM_NAME_RETURN = "OdmFormValue.name AS Form_Name"
    FORM_REPEATING_RETURN = """
    (CASE WHEN OdmFormValue.repeating IS NULL THEN ''
    WHEN OdmFormValue.repeating THEN  'yes' ELSE 'no' END) AS Form_Repeating
    """
    FORM_VERSION_RETURN = "OdmFormLatest.version AS Form_Version"
    ITEM_GROUP_NAME_RETURN = "OdmItemGroupValue.name AS ItemGroup_Name"
    ITEM_GROUP_VERSION_RETURN = "OdmItemGroupLatest.version AS ItemGroup_Version"
    ITEM_NAME_RETURN = "OdmItemValue.name AS Item_Name"
    ITEM_DATATYPE_RETURN = "DataTypeCTCodelistTerm.submission_value AS Item_Datatype"
    ITEM_VERSION_RETURN = "OdmItemLatest.version AS Item_Version"
    ITEM_UNIT_RETURN = (
        "apoc.text.join(COLLECT(DISTINCT UnitDefinitionValue.name), '|') as Item_Units"
    )
    ITEM_CODELIST_RETURN = "CTCodelistAttributesValue.name AS Item_Codelist"
    ITEM_TERM_RETURN = "apoc.text.join(COLLECT(DISTINCT CTCodelistTerm.submission_value), '|') as Item_Terms"

    def get_odm_study_event(self, target_uid: str):
        query = f"""
                WITH "
                    MATCH (OdmStudyEventRoot:OdmStudyEventRoot {{uid: $target_uid}})
                    -[:LATEST_FINAL|LATEST_RETIRED]->(OdmStudyEventValue:OdmStudyEventValue)
                    CALL (OdmStudyEventRoot, OdmStudyEventValue) {{
                        MATCH (OdmStudyEventRoot)-[hv:HAS_VERSION]->(OdmStudyEventValue)
                        WHERE hv.status in ['Final', 'Retired']
                        WITH hv
                        ORDER BY
                            toInteger(split(hv.version, '.')[0]) ASC,
                            toInteger(split(hv.version, '.')[1]) ASC,
                            hv.end_date ASC,
                            hv.start_date ASC
                        WITH collect(hv) as hvs
                        RETURN last(hvs) as OdmStudyEventLatest
                    }}
                    {self.OPTIONAL_FORM_MATCH}
                    {self.OPTIONAL_ITEM_GROUP_MATCH}
                    {self.OPTIONAL_ITEM_MATCH}
                    {self.OPTIONAL_UNIT_DEFINITION_MATCH}
                    {self.OPTIONAL_CODELIST_MATCH}
                    {self.OPTIONAL_CODELIST_TERM_MATCH}
                    {self.OPTIONAL_DATATYPE_MATCH}

                    RETURN
                    {self.STUDY_EVENT_NAME_RETURN},
                    {self.STUDY_EVENT_VERSION_RETURN},
                    {self.FORM_NAME_RETURN},
                    {self.FORM_REPEATING_RETURN},
                    {self.FORM_VERSION_RETURN},
                    {self.ITEM_GROUP_NAME_RETURN},
                    {self.ITEM_GROUP_VERSION_RETURN},
                    {self.ITEM_NAME_RETURN},
                    {self.ITEM_DATATYPE_RETURN},
                    {self.ITEM_VERSION_RETURN},
                    {self.ITEM_UNIT_RETURN},
                    {self.ITEM_CODELIST_RETURN},
                    {self.ITEM_TERM_RETURN}
                " AS query
            """ + self.CSV_EXPORT_QUERY
        result, _ = db.cypher_query(query, {"target_uid": target_uid})

        NotFoundException.raise_if(result[0][1] == 0, "ODM Study Event", target_uid)

        return result[0][0]

    def get_odm_form(self, target_uid: str):
        query = f"""
                WITH "
                    MATCH (OdmFormRoot:OdmFormRoot {{uid: $target_uid}})-[:LATEST_FINAL|LATEST_RETIRED]->(OdmFormValue:OdmFormValue)
                    CALL (OdmFormRoot, OdmFormValue) {{
                        MATCH (OdmFormRoot)-[hv:HAS_VERSION]->(OdmFormValue)
                        WHERE hv.status in ['Final', 'Retired']
                        WITH hv
                        ORDER BY
                            toInteger(split(hv.version, '.')[0]) ASC,
                            toInteger(split(hv.version, '.')[1]) ASC,
                            hv.end_date ASC,
                            hv.start_date ASC
                        WITH collect(hv) as hvs
                        RETURN last(hvs) as OdmFormLatest
                    }}
                    {self.OPTIONAL_ITEM_GROUP_MATCH}
                    {self.OPTIONAL_ITEM_MATCH}
                    {self.OPTIONAL_UNIT_DEFINITION_MATCH}
                    {self.OPTIONAL_CODELIST_MATCH}
                    {self.OPTIONAL_CODELIST_TERM_MATCH}
                    {self.OPTIONAL_DATATYPE_MATCH}

                    RETURN
                    {self.FORM_NAME_RETURN},
                    {self.FORM_REPEATING_RETURN},
                    {self.FORM_VERSION_RETURN},
                    {self.ITEM_GROUP_NAME_RETURN},
                    {self.ITEM_GROUP_VERSION_RETURN},
                    {self.ITEM_NAME_RETURN},
                    {self.ITEM_DATATYPE_RETURN},
                    {self.ITEM_VERSION_RETURN},
                    {self.ITEM_UNIT_RETURN},
                    {self.ITEM_CODELIST_RETURN},
                    {self.ITEM_TERM_RETURN}
                " AS query
            """ + self.CSV_EXPORT_QUERY
        result, _ = db.cypher_query(query, {"target_uid": target_uid})

        NotFoundException.raise_if(result[0][1] == 0, "ODM Form", target_uid)

        return result[0][0]

    def get_odm_item_group(self, target_uid: str):
        query = f"""
                WITH "
                    MATCH (OdmItemGroupRoot:OdmItemGroupRoot {{uid: $target_uid}})
                    -[:LATEST_FINAL|LATEST_RETIRED]->(OdmItemGroupValue:OdmItemGroupValue)
                    CALL (OdmItemGroupRoot, OdmItemGroupValue) {{
                        MATCH (OdmItemGroupRoot)-[hv:HAS_VERSION]->(OdmItemGroupValue)
                        WHERE hv.status in ['Final', 'Retired']
                        WITH hv
                        ORDER BY
                            toInteger(split(hv.version, '.')[0]) ASC,
                            toInteger(split(hv.version, '.')[1]) ASC,
                            hv.end_date ASC,
                            hv.start_date ASC
                        WITH collect(hv) as hvs
                        RETURN last(hvs) as OdmItemGroupLatest
                    }}
                    {self.OPTIONAL_ITEM_MATCH}
                    {self.OPTIONAL_UNIT_DEFINITION_MATCH}
                    {self.OPTIONAL_CODELIST_MATCH}
                    {self.OPTIONAL_CODELIST_TERM_MATCH}
                    {self.OPTIONAL_DATATYPE_MATCH}

                    RETURN
                    {self.ITEM_GROUP_NAME_RETURN},
                    {self.ITEM_GROUP_VERSION_RETURN},
                    {self.ITEM_NAME_RETURN},
                    {self.ITEM_DATATYPE_RETURN},
                    {self.ITEM_VERSION_RETURN},
                    {self.ITEM_UNIT_RETURN},
                    {self.ITEM_CODELIST_RETURN},
                    {self.ITEM_TERM_RETURN}
                " AS query
            """ + self.CSV_EXPORT_QUERY
        result, _ = db.cypher_query(query, {"target_uid": target_uid})

        NotFoundException.raise_if(result[0][1] == 0, "ODM Item Group", target_uid)

        return result[0][0]

    def get_odm_item(self, target_uid: str):
        query = f"""
                WITH "
                    MATCH (OdmItemRoot:OdmItemRoot {{uid: $target_uid}})-[:LATEST_FINAL|LATEST_RETIRED]->(OdmItemValue:OdmItemValue)
                    CALL (OdmItemRoot, OdmItemValue) {{
                        MATCH (OdmItemRoot)-[hv:HAS_VERSION]->(OdmItemValue)
                        WHERE hv.status in ['Final', 'Retired']
                        WITH hv
                        ORDER BY
                            toInteger(split(hv.version, '.')[0]) ASC,
                            toInteger(split(hv.version, '.')[1]) ASC,
                            hv.end_date ASC,
                            hv.start_date ASC
                        WITH collect(hv) as hvs
                        RETURN last(hvs) as OdmItemLatest
                    }}
                    {self.OPTIONAL_UNIT_DEFINITION_MATCH}
                    {self.OPTIONAL_CODELIST_MATCH}
                    {self.OPTIONAL_CODELIST_TERM_MATCH}
                    {self.OPTIONAL_DATATYPE_MATCH}

                    RETURN
                    {self.ITEM_NAME_RETURN},
                    {self.ITEM_DATATYPE_RETURN},
                    {self.ITEM_VERSION_RETURN},
                    {self.ITEM_UNIT_RETURN},
                    {self.ITEM_CODELIST_RETURN},
                    {self.ITEM_TERM_RETURN}
                " AS query
            """ + self.CSV_EXPORT_QUERY
        result, _ = db.cypher_query(query, {"target_uid": target_uid})

        NotFoundException.raise_if(result[0][1] == 0, "ODM Item", target_uid)

        return result[0][0]
