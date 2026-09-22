from typing import Any

from common.utils import validate_page_number_and_page_size
from consumer_api.shared.common import db_pagination_clause, db_sort_clause, query
from consumer_api.v2 import models


def get_studies(
    sort_by: models.SortByStudies = models.SortByStudies.UID,
    sort_order: models.SortOrder = models.SortOrder.ASC,
    page_size: int = 10,
    page_number: int = 1,
) -> list[dict[Any, Any]]:
    validate_page_number_and_page_size(page_number, page_size)

    base_query = """
        MATCH (root:StudyRoot)-[:LATEST]->(val:StudyValue)
        RETURN  root.uid as uid,
                val.study_acronym as acronym,
                val.study_id_prefix as id_prefix,
                val.study_number as number      
        """

    full_query = " ".join(
        [
            base_query,
            db_sort_clause(sort_by.value, sort_order.value),
            db_pagination_clause(page_size, page_number),
        ]
    )
    return query(full_query)
