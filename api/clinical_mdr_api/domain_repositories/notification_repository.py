# pylint: disable=invalid-name
from datetime import datetime

from neomodel import db

from clinical_mdr_api.domain_repositories.models.notification import (
    Notification as NotificationNode,
)
from clinical_mdr_api.models.notification import Notification
from common.exceptions import NotFoundException


class NotificationRepository:
    def _transform_to_model(self, item: NotificationNode) -> Notification:
        return Notification(
            sn=item.sn,
            title=item.title,
            description=item.description,
            notification_type=item.notification_type,
            started_at=item.started_at,
            ended_at=item.ended_at,
            published_at=item.published_at,
        )

    def _transform_to_models(
        self, data: list[list[NotificationNode]]
    ) -> list[Notification]:
        return [self._transform_to_model(elm[0]) for elm in data]

    def retrieve_all_notifications(self) -> list[Notification]:
        rs = db.cypher_query(
            """
            MATCH (n:Notification)
            RETURN n
            """,
            resolve_objects=True,
        )

        return self._transform_to_models(rs[0])

    def retrieve_all_active_notifications(self) -> list[Notification]:
        rs = db.cypher_query(
            """
            MATCH (n:Notification)
            WHERE n.published_at IS NOT NULL
            AND (
                (datetime(n.started_at) IS NULL OR datetime(n.started_at) <= datetime())
                AND 
                (datetime(n.ended_at) IS NULL OR datetime(n.ended_at) >= datetime())
            )
            RETURN n
            """,
            resolve_objects=True,
        )

        return self._transform_to_models(rs[0])

    def retrieve_notification(self, sn: int) -> Notification:
        rs = db.cypher_query(
            """
            MATCH (n:Notification {sn: $sn})
            RETURN n
            """,
            params={"sn": sn},
            resolve_objects=True,
        )

        NotFoundException.raise_if_not(rs[0], "Notification", str(sn), "Serial Number")

        return self._transform_to_model(rs[0][0][0])

    def create_notification(
        self,
        title: str,
        description: str | None,
        notification_type: str,
        started_at: datetime | None,
        ended_at: datetime | None,
        published_at: datetime | None,
    ) -> Notification:
        newest_sn = db.cypher_query(
            """
            MATCH (n:Notification)
            RETURN n.sn ORDER BY n.sn DESC LIMIT 1
            """,
        )

        sn = int(newest_sn[0][0][0]) + 1 if newest_sn[0] else 1

        rs = db.cypher_query(
            """
            CREATE (n:Notification)
            SET
                n.sn = $sn,
                n.title = $title,
                n.description = $description,
                n.notification_type = $notification_type,
                n.started_at = $started_at,
                n.ended_at = $ended_at,
                n.published_at = $published_at
            RETURN n
            """,
            params={
                "sn": sn,
                "title": title,
                "description": description,
                "notification_type": notification_type,
                "started_at": started_at,
                "ended_at": ended_at,
                "published_at": published_at,
            },
            resolve_objects=True,
        )

        return self._transform_to_model(rs[0][0][0])

    def update_notification(
        self,
        sn: int,
        title: str,
        description: str | None,
        notification_type: str,
        started_at: datetime | None,
        ended_at: datetime | None,
        published_at: datetime | None,
    ) -> Notification:
        rs = db.cypher_query(
            """
            MATCH (n:Notification {sn: $sn})
            SET
                n.title = $title,
                n.description = $description,
                n.notification_type = $notification_type,
                n.started_at = $started_at,
                n.ended_at = $ended_at,
                n.published_at = $published_at
            RETURN n
            """,
            params={
                "sn": sn,
                "title": title,
                "description": description,
                "notification_type": notification_type,
                "started_at": started_at,
                "ended_at": ended_at,
                "published_at": published_at,
            },
            resolve_objects=True,
        )

        NotFoundException.raise_if_not(rs[0], "Notification", str(sn), "Serial Number")

        return self._transform_to_model(rs[0][0][0])

    def delete_notification(self, sn: int) -> None:
        db.cypher_query(
            """
            MATCH (n:Notification {sn: $sn})
            DELETE n
            """,
            params={"sn": sn},
        )
