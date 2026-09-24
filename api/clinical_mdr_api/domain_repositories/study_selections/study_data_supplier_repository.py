from neomodel import db

from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_codelist_attributes_repository import (
    CTCodelistAttributesRepository,
)
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.study_selections import (
    StudyDataSupplier,
)
from clinical_mdr_api.models.study_selections.study_selection import (
    StudySelectionDataSupplierInput,
)
from common.auth.user import user
from common.config import settings
from common.exceptions import BusinessLogicException, NotFoundException


class StudyDataSupplierRepository:
    def __init__(self):
        self.author_id = user().id()

    def generate_uid(self) -> str:
        return StudyDataSupplier.get_next_free_uid_and_increment_counter()

    def create(
        self,
        study_uid: str,
        selection_input: StudySelectionDataSupplierInput,
    ):
        rs, _ = db.cypher_query(
            """
            MATCH (study_root:StudyRoot {uid: $study_uid})-[:LATEST]->(study_value:StudyValue)
            -[:HAS_STUDY_DATA_SUPPLIER]->(study_data_supplier:StudySelection:StudyDataSupplier)
            return study_data_supplier.order AS existing_order
            ORDER BY study_data_supplier.order DESC
            LIMIT 1
            """,
            params={"study_uid": study_uid},
        )

        order = rs[0][0] + 1 if rs else 1

        study_data_supplier_uid = self.generate_uid()

        rs = db.cypher_query(
            """
            MATCH (data_supplier_root:DataSupplierRoot {uid: $data_supplier_uid})-[:LATEST]->(data_supplier_value:DataSupplierValue)
            -[:HAS_DATA_SUPPLIER_TYPE]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(data_supplier_type:CTTermRoot)
            MATCH (study_root:StudyRoot {uid: $study_uid})-[:LATEST]->(study_value:StudyValue)
            MATCH (study_root)-[study_has_version:HAS_VERSION WHERE study_has_version.end_date IS NULL]->(study_value)
            CREATE (study_data_supplier:StudySelection:StudyDataSupplier {uid: $study_data_supplier_uid, order: $order, blinded: $blinded})
            CREATE (study_action:StudyAction:Create {author: $author, date: datetime()})
            CREATE (study_data_supplier)-[:HAS_DATA_SUPPLIER]->(data_supplier_value)
            CREATE (study_data_supplier)<-[:AFTER]-(study_action)
            CREATE (study_data_supplier)<-[:HAS_STUDY_DATA_SUPPLIER]-(study_value)
            CREATE (study_root)-[:AUDIT_TRAIL]->(study_action)
            RETURN 
                study_data_supplier.uid AS study_data_supplier_uid,
                study_data_supplier.order AS study_data_supplier_order,
                study_data_supplier.blinded AS blinded,
                data_supplier_root.uid AS data_supplier_uid,
                data_supplier_value.name AS name,
                data_supplier_value.description AS description,
                data_supplier_value.order AS order,
                data_supplier_value.api_base_url AS api_base_url,
                data_supplier_value.ui_base_url AS ui_base_url,
                data_supplier_type.uid AS data_supplier_type_uid,
                study_action.date AS start_date,
                study_action.author AS author_username,
                labels(study_action) AS change_type,
                study_root.uid AS study_uid
            """,
            params={
                "study_uid": study_uid,
                "study_data_supplier_uid": study_data_supplier_uid,
                "data_supplier_uid": selection_input.data_supplier_uid,
                "order": order,
                "author": self.author_id,
                "data_supplier_type_uid": selection_input.study_data_supplier_type_uid,
                "blinded": selection_input.blinded,
            },
        )

        return rs

    def retrieve(
        self,
        study_uid: str | None = None,
        study_data_supplier_uid: str | None = None,
        study_value_version: str | None = None,
    ):
        if study_value_version is None:
            if study_uid is not None:
                query = "MATCH (study_root:StudyRoot {uid:$study_uid})-[:LATEST]->(study_value:StudyValue)"
            else:
                query = (
                    "MATCH (study_root:StudyRoot)-[:LATEST]->(study_value:StudyValue)"
                )
            query += f"""OPTIONAL MATCH (study_value)-[:HAS_STUDY_STANDARD_VERSION]->(:StudyStandardVersion)-[:HAS_CT_PACKAGE]->(ct_package:CTPackage)
            <-[:CONTAINS_PACKAGE]-(:CTCatalogue {{name: "{settings.sdtm_ct_catalogue_name}"}})"""

            query += "MATCH (study_root)-[study_has_version:HAS_VERSION WHERE study_has_version.end_date IS NULL]->(study_value)"
        else:
            if study_uid is not None:
                query = "MATCH (study_root:StudyRoot {uid:$study_uid})-[study_has_version:HAS_VERSION {status:'RELEASED', version:$study_value_version}]->(study_value:StudyValue)"
            else:
                query = "MATCH (study_root:StudyRoot)-[study_has_version:HAS_VERSION {status:'RELEASED', version:$study_value_version}]->(study_value:StudyValue)"

            query += f"""OPTIONAL MATCH (study_value)-[:HAS_STUDY_STANDARD_VERSION]->(:StudyStandardVersion)-[:HAS_CT_PACKAGE]->(ct_package:CTPackage)
            <-[:CONTAINS_PACKAGE]-(:CTCatalogue {{name: "{settings.sdtm_ct_catalogue_name}"}})"""

        effective_date_clause = """<-[:HAS_TERM_ROOT]-(:CTCodelistTerm)<-[ht:HAS_TERM WHERE (ct_package.effective_date IS NULL AND ht.end_date IS NULL)
        OR (ht.start_date <= datetime(toString(date(ct_package.effective_date)) + "T23:59:59.999999999Z") < datetime(ht.end_date))
        OR (ht.end_date IS NULL AND (ht.start_date <= datetime(toString(date(ct_package.effective_date)) + "T23:59:59.999999999Z")))]-(:CTCodelistRoot)"""

        if study_data_supplier_uid is None:
            query += """
            MATCH (study_value)-[:HAS_STUDY_DATA_SUPPLIER]->(study_data_supplier:StudySelection:StudyDataSupplier)
            """
        else:
            query += """
            MATCH (study_value)-[:HAS_STUDY_DATA_SUPPLIER]->(study_data_supplier:StudySelection:StudyDataSupplier {uid: $study_data_supplier_uid})
            """

        query += f"""
            -[:HAS_DATA_SUPPLIER]->(data_supplier_value:DataSupplierValue)
            MATCH (data_supplier_value)-[:HAS_VERSION]-(data_supplier_root:DataSupplierRoot)
            MATCH (study_data_supplier)<-[:AFTER]-(after_study_action:StudyAction)
            OPTIONAL MATCH (study_data_supplier)<-[:BEFORE]-(before_study_action:StudyAction)
            OPTIONAL MATCH (study_data_supplier)-[:HAS_STUDY_DATA_SUPPLIER_TYPE]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(study_data_supplier_type:CTTermRoot)
            {effective_date_clause}
            RETURN DISTINCT
                study_data_supplier.uid AS study_data_supplier_uid,
                study_data_supplier.order AS study_data_supplier_order,
                study_data_supplier.blinded AS blinded,
                data_supplier_root.uid AS data_supplier_uid,
                data_supplier_value.name AS name,
                data_supplier_value.description AS description,
                data_supplier_value.order AS order,
                data_supplier_value.api_base_url AS api_base_url,
                data_supplier_value.ui_base_url AS ui_base_url,
                study_data_supplier_type.uid AS study_data_supplier_type_uid,
                after_study_action.date AS start_date,
                after_study_action.author AS author_username,
                before_study_action.date AS end_date,
                labels(after_study_action) AS change_type,
                study_root.uid AS study_uid,
                study_has_version.version AS study_version,
                datetime(toString(date(ct_package.effective_date)) + "T23:59:59.999999999Z") AS study_effective_date
            ORDER BY study_data_supplier_order ASC, study_data_supplier_uid ASC
            """

        rs = db.cypher_query(
            query,
            params={
                "study_uid": study_uid,
                "study_data_supplier_uid": study_data_supplier_uid,
                "study_value_version": study_value_version,
            },
        )

        return rs

    def retrieve_audit_trail(
        self, study_uid: str, study_data_supplier_uid: str | None = None
    ):
        if study_data_supplier_uid is not None:
            query = f"""
            MATCH (study_root:StudyRoot {{uid: $study_uid}})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(study_data_supplier:StudyDataSupplier {{uid: $study_data_supplier_uid}})
            OPTIONAL MATCH (study_root)-->(study_value:StudyValue)-[:HAS_STUDY_STANDARD_VERSION]->(:StudyStandardVersion)-[:HAS_CT_PACKAGE]->(ct_package:CTPackage)
            <-[:CONTAINS_PACKAGE]-(:CTCatalogue {{name: "{settings.sdtm_ct_catalogue_name}"}})
            WITH study_data_supplier, ct_package
            MATCH (study_data_supplier)-[:AFTER|BEFORE*0..]-(all_sds:StudyDataSupplier)
            WITH DISTINCT all_sds, ct_package
            """
        else:
            query = f"""
            MATCH (study_root:StudyRoot {{uid: $study_uid}})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(all_sds:StudyDataSupplier)
            OPTIONAL MATCH (study_root)-->(study_value:StudyValue)-[:HAS_STUDY_STANDARD_VERSION]->(:StudyStandardVersion)
            -[:HAS_CT_PACKAGE]->(ct_package:CTPackage)<-[:CONTAINS_PACKAGE]-(:CTCatalogue {{name: "{settings.sdtm_ct_catalogue_name}"}})
            WITH DISTINCT all_sds, ct_package
            """

        query += """
            MATCH (all_sds)-[:HAS_DATA_SUPPLIER]->(data_supplier_value:DataSupplierValue)
            MATCH (data_supplier_value)-[:HAS_VERSION]-(data_supplier_root:DataSupplierRoot)
            MATCH (all_sds)<-[:AFTER]-(after_study_action:StudyAction)
            OPTIONAL MATCH (all_sds)<-[:BEFORE]-(before_study_action:StudyAction)
            OPTIONAL MATCH (all_sds)-[:HAS_STUDY_DATA_SUPPLIER_TYPE]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(study_data_supplier_type:CTTermRoot)<-[:HAS_TERM_ROOT]-(:CTCodelistTerm)<-[ht:HAS_TERM WHERE (ct_package.effective_date IS NULL AND ht.end_date IS NULL)
            OR (ht.start_date <= datetime(toString(date(ct_package.effective_date)) + "T23:59:59.999999999Z") < datetime(ht.end_date))
            OR (ht.end_date IS NULL AND (ht.start_date <= datetime(toString(date(ct_package.effective_date)) + "T23:59:59.999999999Z")))]-(:CTCodelistRoot)
            RETURN DISTINCT
                all_sds.uid AS study_data_supplier_uid,
                all_sds.order AS study_data_supplier_order,
                all_sds.blinded AS blinded,
                data_supplier_root.uid AS data_supplier_uid,
                data_supplier_value.name AS name,
                data_supplier_value.description AS description,
                data_supplier_value.order AS order,
                data_supplier_value.api_base_url AS api_base_url,
                data_supplier_value.ui_base_url AS ui_base_url,
                study_data_supplier_type.uid AS study_data_supplier_type_uid,
                after_study_action.date AS start_date,
                after_study_action.author AS author_username,
                before_study_action.date AS end_date,
                labels(after_study_action) AS change_type,
                datetime(toString(date(ct_package.effective_date)) + "T23:59:59.999999999Z") AS study_effective_date
            ORDER BY study_data_supplier_uid DESC, start_date DESC
            """

        rs = db.cypher_query(
            query,
            params={
                "study_uid": study_uid,
                "study_data_supplier_uid": study_data_supplier_uid,
            },
        )

        return rs

    def update(
        self,
        study_uid: str,
        study_data_supplier_uid: str,
        selection_input: StudySelectionDataSupplierInput,
    ):
        rs = db.cypher_query(
            f"""
            MATCH (study_root:StudyRoot {{uid: $study_uid}})-[:LATEST]->(study_value:StudyValue)
            MATCH (study_root)-[study_has_version:HAS_VERSION WHERE study_has_version.end_date IS NULL]->(study_value)
            MATCH (study_value)-[hsds:HAS_STUDY_DATA_SUPPLIER]->(old_study_data_supplier:StudySelection:StudyDataSupplier {{uid: $study_data_supplier_uid}})
            OPTIONAL MATCH (study_value)-[:HAS_STUDY_STANDARD_VERSION]->(:StudyStandardVersion)-[:HAS_CT_PACKAGE]->(ct_package:CTPackage)
            <-[:CONTAINS_PACKAGE]-(:CTCatalogue {{name: "{settings.sdtm_ct_catalogue_name}"}})
            MATCH (data_supplier_root:DataSupplierRoot {{uid: $data_supplier_uid}})-[:LATEST]->(data_supplier_value:DataSupplierValue)
            -[:HAS_DATA_SUPPLIER_TYPE]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(data_supplier_type:CTTermRoot)
            OPTIONAL MATCH (old_study_data_supplier)-[:HAS_STUDY_DATA_SUPPLIER_TYPE]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(study_data_supplier_type:CTTermRoot)<-[:HAS_TERM_ROOT]-(:CTCodelistTerm)<-[ht:HAS_TERM WHERE (ct_package.effective_date IS NULL AND ht.end_date IS NULL)
            OR (ht.start_date <= datetime(toString(date(ct_package.effective_date)) + "T23:59:59.999999999Z") < datetime(ht.end_date))
            OR (ht.end_date IS NULL AND (ht.start_date <= datetime(toString(date(ct_package.effective_date)) + "T23:59:59.999999999Z")))]-(:CTCodelistRoot)
            CREATE (new_study_data_supplier:StudySelection:StudyDataSupplier {{uid: $study_data_supplier_uid, order: old_study_data_supplier.order, blinded: $blinded}})
            CREATE (study_action:StudyAction:Edit {{author: $author, date: datetime()}})
            CREATE (new_study_data_supplier)-[:HAS_DATA_SUPPLIER]->(data_supplier_value)
            CREATE (new_study_data_supplier)<-[:AFTER]-(study_action)
            CREATE (old_study_data_supplier)<-[:BEFORE]-(study_action)
            CREATE (new_study_data_supplier)<-[:HAS_STUDY_DATA_SUPPLIER]-(study_value)
            CREATE (study_root)-[:AUDIT_TRAIL]->(study_action)
            DELETE hsds
            RETURN DISTINCT
                new_study_data_supplier.uid AS study_data_supplier_uid,
                new_study_data_supplier.order AS study_data_supplier_order,
                new_study_data_supplier.blinded AS blinded,
                data_supplier_root.uid AS data_supplier_uid,
                data_supplier_value.name AS name,
                data_supplier_value.description AS description,
                data_supplier_value.order AS order,
                data_supplier_value.api_base_url AS api_base_url,
                data_supplier_value.ui_base_url AS ui_base_url,
                data_supplier_type.uid AS data_supplier_type_uid,
                study_action.date AS start_date,
                study_action.author AS author_username,
                labels(study_action) AS change_type,
                study_root.uid AS study_uid,
                datetime(toString(date(ct_package.effective_date)) + "T23:59:59.999999999Z") AS study_effective_date
            ORDER BY study_data_supplier_order ASC, study_data_supplier_uid ASC
            """,
            params={
                "study_uid": study_uid,
                "data_supplier_uid": selection_input.data_supplier_uid,
                "study_data_supplier_uid": study_data_supplier_uid,
                "author": self.author_id,
                "data_supplier_type_uid": selection_input.study_data_supplier_type_uid,
                "blinded": selection_input.blinded,
            },
        )

        return rs

    def delete(self, study_uid: str, study_data_supplier_uid: str):
        rs = db.cypher_query(
            """
            MATCH (study_root:StudyRoot {uid: $study_uid})-[:LATEST]->(study_value:StudyValue)
            MATCH (study_root)-[study_has_version:HAS_VERSION WHERE study_has_version.end_date IS NULL]->(study_value)
            MATCH (study_value)-[hsds:HAS_STUDY_DATA_SUPPLIER]->(old_study_data_supplier:StudySelection:StudyDataSupplier {uid: $study_data_supplier_uid})
            -[:HAS_DATA_SUPPLIER]->(data_supplier_value:DataSupplierValue)-[:HAS_VERSION]-(data_supplier_root:DataSupplierRoot)
            MATCH (old_study_data_supplier)-[:HAS_STUDY_DATA_SUPPLIER_TYPE]->(ct_term_context:CTTermContext)-[:HAS_SELECTED_TERM]->(study_data_supplier_type:CTTermRoot)
            MERGE (old_study_data_supplier)<-[:BEFORE]-(study_action:StudyAction:Delete {author: $author, date: datetime()})
            MERGE (new_study_data_supplier:StudySelection:StudyDataSupplier {uid: $study_data_supplier_uid, order: old_study_data_supplier.order})<-[:AFTER]-(study_action)
            MERGE (study_root)-[:AUDIT_TRAIL]->(study_action)
            MERGE (old_study_data_supplier)-[:HAS_DATA_SUPPLIER]->(data_supplier_value)
            MERGE (new_study_data_supplier)-[:HAS_DATA_SUPPLIER]->(data_supplier_value)
            MERGE (new_study_data_supplier)-[:HAS_STUDY_DATA_SUPPLIER_TYPE]->(ct_term_context)
            WITH *
            MATCH (old_study_data_supplier)<-[hsds:HAS_STUDY_DATA_SUPPLIER]-(study_value)
            DELETE hsds
            RETURN DISTINCT new_study_data_supplier.uid AS study_data_supplier_uid, old_study_data_supplier.order AS old_order
            """,
            params={
                "study_uid": study_uid,
                "study_data_supplier_uid": study_data_supplier_uid,
                "author": self.author_id,
            },
        )

        if rs[0] and rs[0][0]:
            db.cypher_query(
                """
                MATCH (study_root:StudyRoot {uid: $study_uid})-[:LATEST]->(study_value:StudyValue)
                MATCH (study_root)-[study_has_version:HAS_VERSION WHERE study_has_version.end_date IS NULL]->(study_value)
                MATCH (study_value)-[:HAS_STUDY_DATA_SUPPLIER]->(old_study_data_supplier:StudySelection:StudyDataSupplier WHERE old_study_data_supplier.order > $old_order)
                -[:HAS_DATA_SUPPLIER]->(data_supplier_value:DataSupplierValue)-[:HAS_VERSION]-(data_supplier_root:DataSupplierRoot)
                MATCH (old_study_data_supplier)-[:HAS_STUDY_DATA_SUPPLIER_TYPE]->(ct_term_context:CTTermContext)-[:HAS_SELECTED_TERM]->(study_data_supplier_type:CTTermRoot)
                WITH DISTINCT data_supplier_value, data_supplier_root, ct_term_context, study_data_supplier_type, old_study_data_supplier, study_root, study_value
                CREATE (new_study_data_supplier:StudySelection:StudyDataSupplier {uid: old_study_data_supplier.uid, order: old_study_data_supplier.order - 1})
                CREATE (study_action:StudyAction:Edit {author: $author, date: datetime()})
                CREATE (new_study_data_supplier)-[:HAS_DATA_SUPPLIER]->(data_supplier_value)
                CREATE (new_study_data_supplier)<-[:AFTER]-(study_action)
                CREATE (old_study_data_supplier)<-[:BEFORE]-(study_action)
                CREATE (new_study_data_supplier)<-[:HAS_STUDY_DATA_SUPPLIER]-(study_value)
                CREATE (study_root)-[:AUDIT_TRAIL]->(study_action)
                CREATE (new_study_data_supplier)-[:HAS_STUDY_DATA_SUPPLIER_TYPE]->(ct_term_context)
                WITH *
                MATCH (old_study_data_supplier)<-[hsds:HAS_STUDY_DATA_SUPPLIER]-(study_value)
                DELETE hsds
                RETURN
                    new_study_data_supplier.uid AS study_data_supplier_uid,
                    new_study_data_supplier.order AS study_data_supplier_order,
                    data_supplier_root.uid AS data_supplier_uid,
                    data_supplier_value.name AS name,
                    data_supplier_value.description AS description,
                    data_supplier_value.order AS order,
                    data_supplier_value.api_base_url AS api_base_url,
                    data_supplier_value.ui_base_url AS ui_base_url,
                    study_data_supplier_type.uid AS study_data_supplier_type_uid,
                    study_action.date AS start_date,
                    study_action.author AS author_username,
                    labels(study_action) AS change_type,
                    study_root.uid AS study_uid,
                    old_study_data_supplier.order AS old_order
                """,
                params={
                    "study_uid": study_uid,
                    "old_order": rs[0][0][1],
                    "author": self.author_id,
                },
            )

        return rs

    def set_order(self, study_uid: str, study_data_supplier_uid: str, order: int):
        rs, _ = db.cypher_query(
            """
            MATCH (study_root:StudyRoot {uid: $study_uid})-[:LATEST]->(study_value:StudyValue)
            -[:HAS_STUDY_DATA_SUPPLIER]-(study_data_supplier:StudySelection:StudyDataSupplier)
            RETURN
                study_data_supplier.uid AS study_data_supplier_uid,
                study_data_supplier.order AS study_data_supplier_order
            """,
            params={"study_uid": study_uid},
        )

        existing_count = len(rs)

        if order == next(
            (current[1] for current in rs if current[0] == study_data_supplier_uid),
            None,
        ):
            raise BusinessLogicException(msg="Order is the same as the current order.")

        if existing_count == 1:
            raise BusinessLogicException(
                msg="Cannot set order when there is only one Study Data Supplier."
            )

        if order < 1 or order > existing_count:
            order = existing_count + 1

        rs = db.cypher_query(
            """
            MATCH (study_root:StudyRoot {uid: $study_uid})-[:LATEST]->(study_value:StudyValue)
            MATCH (study_root)-[study_has_version:HAS_VERSION WHERE study_has_version.end_date IS NULL]->(study_value)
            MATCH (study_value)-[:HAS_STUDY_DATA_SUPPLIER]->(old_study_data_supplier:StudySelection:StudyDataSupplier {uid: $study_data_supplier_uid})
            -[:HAS_DATA_SUPPLIER]->(data_supplier_value:DataSupplierValue)-[:HAS_VERSION]-(data_supplier_root:DataSupplierRoot)
            OPTIONAL MATCH (old_study_data_supplier)-[:HAS_STUDY_DATA_SUPPLIER_TYPE]->(ct_term_context:CTTermContext)-[:HAS_SELECTED_TERM]->(study_data_supplier_type:CTTermRoot)
            WITH DISTINCT data_supplier_value, data_supplier_root, ct_term_context, study_data_supplier_type, old_study_data_supplier, study_root, study_value
            CREATE (new_study_data_supplier:StudySelection:StudyDataSupplier {uid: $study_data_supplier_uid, order: $order})
            CREATE (study_action:StudyAction:Edit {author: $author, date: datetime()})
            CREATE (new_study_data_supplier)-[:HAS_DATA_SUPPLIER]->(data_supplier_value)
            CREATE (new_study_data_supplier)<-[:AFTER]-(study_action)
            CREATE (old_study_data_supplier)<-[:BEFORE]-(study_action)
            CREATE (new_study_data_supplier)<-[:HAS_STUDY_DATA_SUPPLIER]-(study_value)
            CREATE (study_root)-[:AUDIT_TRAIL]->(study_action)
            CREATE (new_study_data_supplier)-[:HAS_STUDY_DATA_SUPPLIER_TYPE]->(ct_term_context)
            WITH *
            MATCH (old_study_data_supplier)<-[hsds:HAS_STUDY_DATA_SUPPLIER]-(study_value)
            DELETE hsds
            RETURN
                new_study_data_supplier.uid AS study_data_supplier_uid,
                new_study_data_supplier.order AS study_data_supplier_order,
                data_supplier_root.uid AS data_supplier_uid,
                data_supplier_value.name AS name,
                data_supplier_value.description AS description,
                data_supplier_value.order AS order,
                data_supplier_value.api_base_url AS api_base_url,
                data_supplier_value.ui_base_url AS ui_base_url,
                study_data_supplier_type.uid AS study_data_supplier_type_uid,
                study_action.date AS start_date,
                study_action.author AS author_username,
                labels(study_action) AS change_type,
                study_root.uid AS study_uid,
                old_study_data_supplier.order AS old_order
            """,
            params={
                "study_uid": study_uid,
                "study_data_supplier_uid": study_data_supplier_uid,
                "order": order,
                "author": self.author_id,
            },
        )

        if not rs or not rs[0]:
            raise NotFoundException(
                msg="Study Data Supplier not found for the given Study."
            )

        if order < rs[0][0][13]:
            where_stmt = "WHERE old_study_data_supplier.order >= $order AND old_study_data_supplier.order < $old_order AND NOT old_study_data_supplier.uid = $study_data_supplier_uid"
            operator = "+"
        else:
            where_stmt = "WHERE old_study_data_supplier.order <= $order AND old_study_data_supplier.order > $old_order AND NOT old_study_data_supplier.uid = $study_data_supplier_uid"
            operator = "-"

        db.cypher_query(
            f"""
            MATCH (study_root:StudyRoot {{uid: $study_uid}})-[:LATEST]->(study_value:StudyValue)
            MATCH (study_root)-[study_has_version:HAS_VERSION WHERE study_has_version.end_date IS NULL]->(study_value)
            MATCH (study_value)-[:HAS_STUDY_DATA_SUPPLIER]->(old_study_data_supplier:StudySelection:StudyDataSupplier {where_stmt})
            -[:HAS_DATA_SUPPLIER]->(data_supplier_value:DataSupplierValue)-[:HAS_VERSION]-(data_supplier_root:DataSupplierRoot)
            OPTIONAL MATCH (old_study_data_supplier)-[:HAS_STUDY_DATA_SUPPLIER_TYPE]->(ct_term_context:CTTermContext)-[:HAS_SELECTED_TERM]->(:CTTermRoot)
            WITH DISTINCT data_supplier_value, data_supplier_root, ct_term_context, old_study_data_supplier, study_root, study_value
            CREATE (new_study_data_supplier:StudySelection:StudyDataSupplier {{uid: old_study_data_supplier.uid, order: old_study_data_supplier.order {operator} 1}})
            CREATE (study_action:StudyAction:Edit {{author: $author, date: datetime()}})
            CREATE (new_study_data_supplier)-[:HAS_DATA_SUPPLIER]->(data_supplier_value)
            CREATE (new_study_data_supplier)<-[:AFTER]-(study_action)
            CREATE (old_study_data_supplier)<-[:BEFORE]-(study_action)
            CREATE (new_study_data_supplier)<-[:HAS_STUDY_DATA_SUPPLIER]-(study_value)
            CREATE (study_root)-[:AUDIT_TRAIL]->(study_action)
            CREATE (new_study_data_supplier)-[:HAS_STUDY_DATA_SUPPLIER_TYPE]->(ct_term_context)
            WITH *
            MATCH (old_study_data_supplier)<-[hsds:HAS_STUDY_DATA_SUPPLIER]-(study_value)
            DELETE hsds
            RETURN new_study_data_supplier.uid AS study_data_supplier_uid
            """,
            params={
                "study_uid": study_uid,
                "study_data_supplier_uid": study_data_supplier_uid,
                "order": order,
                "old_order": rs[0][0][13],
                "author": self.author_id,
            },
        )

        return rs

    def connect_data_supplier_type(
        self,
        study_uid: str,
        data_supplier_type_uid: str | None,
        study_data_supplier_uid: str,
    ):
        if data_supplier_type_uid is not None:
            ct_term_root = CTTermRoot.nodes.get(uid=data_supplier_type_uid)
            # Use Cypher to find the CURRENT node (connected to LATEST StudyValue)
            results, _ = db.cypher_query(
                """
                MATCH (sr:StudyRoot {uid: $study_uid})-[:LATEST]->(sv:StudyValue)
                -[:HAS_STUDY_DATA_SUPPLIER]->(sds:StudyDataSupplier {uid: $sds_uid})
                RETURN sds
                """,
                params={"study_uid": study_uid, "sds_uid": study_data_supplier_uid},
            )
            if results and results[0]:
                study_data_supplier_node = StudyDataSupplier.inflate(results[0][0])
                selected_term_node = CTCodelistAttributesRepository().get_or_create_selected_term(
                    ct_term_root,
                    codelist_submission_value=settings.data_supplier_type_cl_submval,
                )
                study_data_supplier_node.has_study_data_supplier_type.connect(
                    selected_term_node
                )
