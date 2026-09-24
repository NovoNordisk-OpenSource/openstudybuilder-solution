from neomodel import db

from clinical_mdr_api.models.meta_study_field import MetaStudyField


class MetaStudyFieldService:
    """Read-only service for predefined `MetaStudyField` nodes."""

    @staticmethod
    def get_all() -> list[MetaStudyField]:
        """Return one row per distinct `osb_field_name` across all
        `MetaStudyField` nodes, ordered by `osb_field_name`. Multiple MSF
        nodes may share an `osb_field_name` (one per semantic data type);
        for the aggregated row the first non-null `osb_page_reference`
        among them is returned."""
        rows, _ = db.cypher_query("""
            MATCH (msf:MetaStudyField)
            WHERE msf.osb_field_name IS NOT NULL
               OR msf.osb_page_reference IS NOT NULL
            WITH msf.osb_field_name AS osb_field_name,
                 collect(DISTINCT msf.osb_page_reference) AS page_refs
            WITH osb_field_name,
                 head([p IN page_refs WHERE p IS NOT NULL]) AS osb_page_reference
            RETURN osb_field_name, osb_page_reference
            ORDER BY osb_field_name
            """)
        return [
            MetaStudyField(
                osb_field_name=row[0],
                osb_page_reference=row[1],
            )
            for row in rows
        ]
