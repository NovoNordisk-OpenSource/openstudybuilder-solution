# pylint: disable=invalid-name
from neomodel import db

from clinical_mdr_api.domain_repositories.models.data_completeness_tag import (
    DataCompletenessTag as DataCompletenessTagNode,
)
from clinical_mdr_api.models.data_completeness_tag import DataCompletenessTag
from common.exceptions import NotFoundException


class DataCompletenessTagRepository:
    def _transform_to_model(self, item: DataCompletenessTagNode) -> DataCompletenessTag:
        return DataCompletenessTag(
            uid=item.uid,
            name=item.name,
        )

    def _transform_to_models(
        self, data: list[list[DataCompletenessTagNode]]
    ) -> list[DataCompletenessTag]:
        return [self._transform_to_model(elm[0]) for elm in data]

    def retrieve_all_data_completeness_tags(self) -> list[DataCompletenessTag]:
        rs = db.cypher_query(
            """
            MATCH (n:DataCompletenessTag)
            RETURN n
            """,
            resolve_objects=True,
        )

        return self._transform_to_models(rs[0])

    def find_data_completeness_tag_by_name(
        self, name: str
    ) -> DataCompletenessTag | None:
        rs = db.cypher_query(
            """
            MATCH (n:DataCompletenessTag {name: $name})
            RETURN n
            """,
            params={"name": name},
            resolve_objects=True,
        )

        if rs[0]:
            return self._transform_to_model(rs[0][0][0])

        return None

    def create_data_completeness_tag(
        self,
        name: str,
    ) -> DataCompletenessTag:
        uid = DataCompletenessTagNode.get_next_free_uid_and_increment_counter()

        rs = db.cypher_query(
            """
            CREATE (n:DataCompletenessTag)
            SET
                n.uid = $uid,
                n.name = $name
            RETURN n
            """,
            params={
                "uid": uid,
                "name": name,
            },
            resolve_objects=True,
        )

        return self._transform_to_model(rs[0][0][0])

    def update_data_completeness_tag(self, uid: str, name: str) -> DataCompletenessTag:
        rs = db.cypher_query(
            """
            MATCH (n:DataCompletenessTag {uid: $uid})
            SET n.name = $name
            RETURN n
            """,
            params={"uid": uid, "name": name},
            resolve_objects=True,
        )

        NotFoundException.raise_if_not(rs[0], "Data Completeness Tag", uid, "UID")

        return self._transform_to_model(rs[0][0][0])

    def delete_data_completeness_tag(self, uid: str) -> None:
        db.cypher_query(
            """
            MATCH (n:DataCompletenessTag {uid: $uid})
            DELETE n
            """,
            params={"uid": uid},
        )

    def get_tags_for_study(self, study_uid: str) -> list[DataCompletenessTag]:
        rs = db.cypher_query(
            """
            MATCH (sr:StudyRoot {uid: $study_uid})-[:HAS_COMPLETENESS_TAG]->(t:DataCompletenessTag)
            RETURN t
            """,
            params={"study_uid": study_uid},
            resolve_objects=True,
        )

        return self._transform_to_models(rs[0])

    def assign_tag_to_study(self, study_uid: str, tag_uid: str) -> DataCompletenessTag:
        rs = db.cypher_query(
            """
            MATCH (sr:StudyRoot {uid: $study_uid})
            MATCH (t:DataCompletenessTag {uid: $tag_uid})
            MERGE (sr)-[:HAS_COMPLETENESS_TAG]->(t)
            RETURN t
            """,
            params={"study_uid": study_uid, "tag_uid": tag_uid},
            resolve_objects=True,
        )

        NotFoundException.raise_if_not(rs[0], "Data Completeness Tag", tag_uid, "UID")

        return self._transform_to_model(rs[0][0][0])

    def remove_tag_from_study(self, study_uid: str, tag_uid: str) -> None:
        db.cypher_query(
            """
            MATCH (sr:StudyRoot {uid: $study_uid})-[r:HAS_COMPLETENESS_TAG]->(t:DataCompletenessTag {uid: $tag_uid})
            DELETE r
            """,
            params={"study_uid": study_uid, "tag_uid": tag_uid},
        )
