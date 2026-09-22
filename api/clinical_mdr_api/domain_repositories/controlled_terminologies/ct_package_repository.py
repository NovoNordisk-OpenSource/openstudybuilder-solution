from datetime import date, datetime
from typing import Collection

from neomodel import db
from neomodel.exceptions import UniqueProperty

from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTCatalogue,
    CTPackage,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_package import CTPackageAR
from clinical_mdr_api.models.controlled_terminologies.ct_package import (
    CTPackage as CTPackageModel,
)
from clinical_mdr_api.services.user_info import UserInfoService
from common.config import settings
from common.exceptions import AlreadyExistsException, NotFoundException
from common.telemetry import trace_calls


class CTPackageRepository:
    def package_exists(self, package_name: str) -> bool:
        package_node = CTPackage.nodes.get_or_none(name=package_name)
        return bool(package_node)

    @trace_calls
    def find_all(
        self,
        catalogue_name: str | None,
        standards_only: bool = True,
        sponsor_only: bool = False,
    ) -> Collection[CTPackageAR]:
        where_clause_elements = []
        if sponsor_only:
            standards_only = False
        if catalogue_name is not None:
            where_clause_elements.append("catalogue.name=$catalogue_name")
        if standards_only:
            where_clause_elements.append("NOT EXISTS((package)-[:EXTENDS_PACKAGE]->())")
        where_clause = (
            f"WHERE {' AND '.join(where_clause_elements)}"
            if len(where_clause_elements) > 0
            else ""
        )

        query = f"""
            MATCH (catalogue:CTCatalogue)-[:CONTAINS_PACKAGE]->(package:CTPackage)
            {where_clause}
            {"OPTIONAL" if not sponsor_only else ""} MATCH (package)-[:EXTENDS_PACKAGE]->(extends:CTPackage)
            CALL (package) {{
                OPTIONAL MATCH (author: User)
                WHERE author.user_id = package.author_id
                RETURN coalesce(author.username, package.author_id) AS author_username
            }}
            RETURN  package,
                    extends.uid AS extends_package,
                    author_username
            ORDER BY catalogue.name, package.effective_date
            """

        result, _ = db.cypher_query(
            query, {"catalogue_name": catalogue_name}, resolve_objects=True
        )

        if len(result) == 0:
            return []
        # projecting results to CTPackageAR instances
        ct_packages: list[CTPackageAR] = [
            CTPackageAR.from_repository_values(
                uid=ct_package[0].uid,
                catalogue_name=ct_package[0].contains_package.single().name,
                name=ct_package[0].name,
                label=ct_package[0].label,
                description=ct_package[0].description,
                href=ct_package[0].href,
                registration_status=ct_package[0].registration_status,
                source=ct_package[0].source,
                extends_package=ct_package[1] if len(ct_package) > 1 else None,
                import_date=ct_package[0].import_date,
                effective_date=ct_package[0].effective_date,
                author_id=ct_package[0].author_id,
                author_username=ct_package[2],
            )
            for ct_package in result
        ]
        return ct_packages

    @trace_calls
    def find_by_uid(
        self, uid: str | None, sponsor_only: bool = False
    ) -> CTPackageModel | None:
        query = f"""
            MATCH (catalogue:CTCatalogue)-[:CONTAINS_PACKAGE]->(package:CTPackage)
            WHERE package.uid = $uid
            {"OPTIONAL" if not sponsor_only else ""} MATCH (package)-[:EXTENDS_PACKAGE]->(extends:CTPackage)
            CALL (package) {{
                OPTIONAL MATCH (author: User)
                WHERE author.user_id = package.author_id
                RETURN coalesce(author.username, package.author_id) AS author_username
            }}
            RETURN  package,
                    extends.uid AS extends_package,
                    author_username
            ORDER BY catalogue.name, package.effective_date
            """

        res = db.cypher_query(query, {"uid": uid}, resolve_objects=True)[0]
        ct_package = res[0] if res else None

        if not ct_package:
            return None
        # projecting results to CTPackageAR instances
        ct_package_ar: CTPackageModel = CTPackageModel.from_ct_package_ar(
            CTPackageAR.from_repository_values(
                uid=ct_package[0].uid,
                catalogue_name=ct_package[0].contains_package.single().name,
                name=ct_package[0].name,
                label=ct_package[0].label,
                description=ct_package[0].description,
                href=ct_package[0].href,
                registration_status=ct_package[0].registration_status,
                source=ct_package[0].source,
                extends_package=ct_package[1] if len(ct_package) > 1 else None,
                import_date=ct_package[0].import_date,
                effective_date=ct_package[0].effective_date,
                author_id=ct_package[0].author_id,
                author_username=ct_package[2],
            )
        )
        return ct_package_ar

    def count_all(self) -> int:
        """
        Returns the count of CT Packages in the database

        :return: int - count of CT Packages
        """
        return len(CTPackage.nodes)

    @trace_calls
    def find_by_catalogue_and_date(
        self, catalogue_name: str, package_date: date
    ) -> CTPackageAR | None:
        query = """
            MATCH (:CTCatalogue {name: $catalogue_name})-[:CONTAINS_PACKAGE]->(package:CTPackage)
            WHERE date(package.effective_date) = date($date)

            CALL (package) {
                OPTIONAL MATCH (author: User)
                WHERE author.user_id = package.author_id
                RETURN coalesce(author.username, package.author_id) AS author_username 
            }
            RETURN  package, 
                    author_username
            """
        result, _ = db.cypher_query(
            query,
            {"catalogue_name": catalogue_name, "date": package_date},
            resolve_objects=True,
        )
        if len(result) > 0 and len(result[0]) > 0:
            ct_package = result[0][0]
            author_username = result[0][1]
            return CTPackageAR.from_repository_values(
                uid=ct_package.uid,
                catalogue_name=ct_package.contains_package.single().name,
                name=ct_package.name,
                label=ct_package.label,
                description=ct_package.description,
                href=ct_package.href,
                registration_status=ct_package.registration_status,
                source=ct_package.source,
                import_date=ct_package.import_date,
                effective_date=ct_package.effective_date,
                author_id=ct_package.author_id,
                author_username=author_username,
                extends_package=None,
            )
        return None

    @trace_calls
    def create_sponsor_package(
        self,
        extends_package: str,
        effective_date: date,
        author_id: str,
        library_name: str = settings.sponsor_library_name,
    ) -> CTPackageAR:
        # First, get parent_package node
        extends_package_node: CTPackage = CTPackage.nodes.get_or_none(
            uid=extends_package
        )

        # Throw a NotFoundError if it does not exist
        NotFoundException.raise_if_not(
            extends_package_node, "Parent Package", extends_package
        )
        catalogue_node: CTCatalogue = extends_package_node.contains_package.single()

        # Create the new package
        sponsor_package_uid = f"{library_name} {catalogue_node.name} {effective_date.strftime('%Y-%m-%d')}"

        # Pre-creation validation: check if a package with the same name already exists
        # This provides an additional safety layer beyond the database constraint
        existing_package = CTPackage.nodes.get_or_none(name=sponsor_package_uid)
        if existing_package is not None:
            raise AlreadyExistsException(
                msg=f"A {library_name} CTPackage already exists for this date"
            )

        sponsor_package = CTPackage(
            uid=sponsor_package_uid,
            name=sponsor_package_uid,
            description=f"{library_name} package for {extends_package}, as of {effective_date.strftime('%Y-%m-%d')}",
            import_date=datetime.now(),
            effective_date=effective_date,
            author_id=author_id,
        )
        try:
            sponsor_package.save()
        except UniqueProperty as exc:
            raise AlreadyExistsException(
                msg=f"A {library_name} CTPackage already exists for this date"
            ) from exc
        # Connect the new package to its parent and the catalogue node
        sponsor_package.extends_package.connect(extends_package_node)
        catalogue_node.contains_package.connect(sponsor_package)

        return CTPackageAR.from_repository_values(
            uid=sponsor_package.uid,
            catalogue_name=catalogue_node.name,
            name=sponsor_package.name,
            description=sponsor_package.description,
            label=sponsor_package.label,
            href=sponsor_package.href,
            registration_status=sponsor_package.registration_status,
            source=sponsor_package.source,
            import_date=sponsor_package.import_date,
            effective_date=sponsor_package.effective_date,
            author_id=author_id,
            author_username=UserInfoService.get_author_username_from_id(author_id),
            extends_package=extends_package,
        )

    def close(self) -> None:
        # Our repository guidelines state that repos should have a close method
        # But nothing needs to be done in this one
        pass
