import logging
from datetime import datetime
from threading import Lock
from typing import Collection

from cachetools import TTLCache, cached
from cachetools.keys import hashkey
from neo4j.exceptions import CypherSyntaxError
from neomodel import db

from clinical_mdr_api.domain_repositories.generic_repository import (
    RepositoryClosureData,
)
from clinical_mdr_api.domain_repositories.models.comments import (
    CommentReply,
    CommentReplyVersion,
    CommentThread,
    CommentThreadVersion,
    CommentTopic,
)
from clinical_mdr_api.domains.comments.comments import (
    CommentReplyAR,
    CommentThreadAR,
    CommentThreadStatus,
    CommentTopicAR,
)
from clinical_mdr_api.repositories._utils import sb_clear_cache
from clinical_mdr_api.services.user_info import UserInfoService
from common import exceptions
from common.config import settings
from common.utils import convert_to_datetime, validate_max_skip_clause

log = logging.getLogger(__name__)


class CommentsRepository:
    cache_store_item_by_uid = TTLCache(
        maxsize=settings.cache_max_size, ttl=settings.cache_ttl
    )
    lock_store_item_by_uid = Lock()

    def generate_topic_uid(self) -> str:
        return CommentTopic.get_next_free_uid_and_increment_counter()

    def generate_thread_uid(self) -> str:
        return CommentThread.get_next_free_uid_and_increment_counter()

    def generate_reply_uid(self) -> str:
        return CommentReply.get_next_free_uid_and_increment_counter()

    def get_hashkey(
        self,
        uid: str,
    ):
        """
        Returns a hash key that will be used for mapping objects stored in cache,
        which ultimately determines whether a method invocation is a hit or miss.
        """
        return hashkey(
            str(type(self)),
            uid,
        )

    @cached(cache=cache_store_item_by_uid, key=get_hashkey, lock=lock_store_item_by_uid)
    def find_comment_thread_by_uid(self, uid: str) -> CommentThreadAR | None:
        node: CommentThread = CommentThread.nodes.get_or_none(uid=uid, is_deleted=False)
        if node is not None:
            item = CommentThreadAR.from_repository_values(
                uid=node.uid,
                text=node.text,
                topic_path=node.topic.single().topic_path,
                author_id=node.author_id,
                author_display_name=UserInfoService.get_author_name_from_id(
                    node.author_id
                ),
                status=node.status,
                created_at=node.created_at,
                modified_at=node.modified_at,
                status_modified_at=node.status_modified_at,
                status_modified_by=node.status_modified_by,
                deleted_at=node.deleted_at,
            )
            return item
        return None

    @cached(cache=cache_store_item_by_uid, key=get_hashkey, lock=lock_store_item_by_uid)
    def find_comment_reply_by_uid(self, uid: str) -> CommentReplyAR | None:
        nodes = CommentReply.nodes.get_or_none(
            uid=uid, is_deleted=False, reply_to__is_deleted=False
        )
        if nodes is not None:
            node = nodes[0]
            item = CommentReplyAR.from_repository_values(
                uid=node.uid,
                text=node.text,
                comment_thread_uid=node.reply_to.single().uid,
                author_id=node.author_id,
                author_display_name=UserInfoService.get_author_name_from_id(
                    node.author_id
                ),
                created_at=node.created_at,
                modified_at=node.modified_at,
                deleted_at=node.deleted_at,
            )
            return item
        return None

    def find_topic_by_path(self, path: str) -> CommentTopicAR | None:
        node = CommentTopic.nodes.first_or_none(topic_path=path)
        if node is not None:
            topic = CommentTopicAR.from_repository_values(
                uid=node.uid,
                topic_path=node.topic_path,
            )
            return topic
        return None

    @sb_clear_cache(caches=["cache_store_item_by_uid"])
    def save_comment_thread(self, item: CommentThreadAR) -> None:
        repository_closure_data = item.repository_closure_data

        if repository_closure_data is None:
            node = CommentThread(
                uid=item.uid,
                text=item.text,
                author_id=item.author_id,
                status=item.status.value,
                created_at=item.created_at,
                modified_at=item.modified_at,
                deleted_at=item.deleted_at,
                status_modified_at=item.status_modified_at,
                status_modified_by=item.status_modified_by,
                topic_path=item.topic_path,
            )
            node.save()
            node.topic.connect(
                CommentTopic.nodes.get_or_none(topic_path=item.topic_path)
            )
        else:
            raise NotImplementedError

    @sb_clear_cache(caches=["cache_store_item_by_uid"])
    def edit_comment_thread(
        self,
        item_latest: CommentThreadAR,
        item_previous: CommentThreadAR,
        author_id: str,
    ) -> None:
        now = datetime.now()

        # Update the latest version of comment thread (i.e. the existing CommentThread node)
        node_latest = CommentThread.nodes.get_or_none(uid=item_latest.uid)
        node_latest.text = item_latest.text
        node_latest.status = item_latest.status.value
        node_latest.modified_at = (
            item_latest.modified_at if item_latest.text == item_previous.text else now
        )
        node_latest.status_modified_at = (
            item_latest.status_modified_at
            if item_latest.status == item_previous.status
            else now
        )
        node_latest.status_modified_by = (
            item_latest.status_modified_by
            if item_latest.status == item_previous.status
            else author_id
        )
        node_latest.save()
        previous_versions = sorted(
            node_latest.previous_version.all(), key=lambda x: x.to_ts, reverse=True
        )

        # Create a new CommentThreadVersion node representing the version of comment thread before the edit
        node_previous = CommentThreadVersion(
            text=item_previous.text,
            status=item_previous.status.value,
            status_modified_by=item_previous.status_modified_by,
            from_ts=(
                previous_versions[0].to_ts
                if previous_versions
                else node_latest.created_at
            ),
            to_ts=now,
        )
        node_previous.save()
        node_latest.previous_version.connect(node_previous)

    @sb_clear_cache(caches=["cache_store_item_by_uid"])
    def save_comment_reply(self, item: CommentReplyAR) -> None:
        repository_closure_data = item.repository_closure_data

        if repository_closure_data is None:
            node = CommentReply(
                uid=item.uid,
                text=item.text,
                author_id=item.author_id,
                created_at=item.created_at,
                modified_at=item.modified_at,
                deleted_at=item.deleted_at,
            )
            node.save()
            node.reply_to.connect(
                CommentThread.nodes.get_or_none(uid=item.comment_thread_uid)
            )
        else:
            raise NotImplementedError

    @sb_clear_cache(caches=["cache_store_item_by_uid"])
    def edit_comment_reply(
        self, item_latest: CommentReplyAR, item_previous: CommentReplyAR
    ) -> None:
        now = datetime.now()

        # Update the latest version of comment reply (i.e. the existing CommentReply node)
        node_latest = CommentReply.nodes.get_or_none(uid=item_latest.uid)
        node_latest.text = item_latest.text
        node_latest.modified_at = now
        node_latest.save()
        previous_versions = sorted(
            node_latest.previous_version.all(), key=lambda x: x.to_ts, reverse=True
        )

        # Create a new CommentReplyVersion node representing the version of comment reply before the edit
        node_previous = CommentReplyVersion(
            text=item_previous.text,
            from_ts=(
                previous_versions[0].to_ts
                if previous_versions
                else node_latest.created_at
            ),
            to_ts=now,
        )
        node_previous.save()
        node_latest.previous_version.connect(node_previous)

    @sb_clear_cache(caches=["cache_store_item_by_uid"])
    def save_comment_topic(self, item: CommentTopicAR) -> None:
        repository_closure_data = item.repository_closure_data

        if repository_closure_data is None:
            node = CommentTopic(
                uid=item.uid,
                topic_path=item.topic_path,
            )
            node.save()
        else:
            raise NotImplementedError

    def find_all_comment_threads(
        self,
        topic_path: str | None = None,
        topic_path_partial_match: bool = False,
        status: CommentThreadStatus | None = None,
        page_number: int = 1,
        page_size: int = 0,
    ) -> tuple[list[CommentThreadAR], int]:
        validate_max_skip_clause(page_number=page_number, page_size=page_size)
        params = {
            "topic_path": topic_path,
            "skip": (page_number - 1) * page_size,
            "limit": page_size,
        }

        topic_clause = ""
        if topic_path is not None:
            if topic_path_partial_match:
                topic_clause = (
                    "AND toLower(topic.topic_path) CONTAINS toLower($topic_path) "
                )
            else:
                topic_clause = "AND toLower(topic.topic_path) = toLower($topic_path) "

        if status is None:
            status_clause = ""
        else:
            status_clause = "AND toLower(thread.status) = toLower($status) "
            params["status"] = status.value

        full_query = f"""
            MATCH (topic:CommentTopic)<-[:TOPIC]-(thread:CommentThread)
            WHERE thread.is_deleted = false
            {topic_clause}
            {status_clause}

            WITH topic, thread
            OPTIONAL MATCH  (topic:CommentTopic)<-[:TOPIC]-(thread:CommentThread)<-[:REPLY_TO]-(reply:CommentReply)
            WHERE reply.is_deleted = false

            WITH topic, thread, reply,
                coalesce(head([(user:User)-[*0]-() WHERE user.user_id=reply.author_id | user.name]), reply.author_id) AS reply_author_display_name
            WITH topic, thread, COLLECT(reply {{.*, author_display_name: reply_author_display_name}}) as replies
            ORDER BY thread.created_at ASC
            SKIP $skip LIMIT $limit
            RETURN  topic.uid,
                    topic.topic_path, 
                    thread.uid,
                    thread.text,
                    thread.author_id,
                    coalesce(head([(user:User)-[*0]-() WHERE user.user_id=thread.author_id | user.name]), thread.author_id) AS thread_author_display_name,
                    thread.status, 
                    thread.created_at, 
                    thread.modified_at, 
                    thread.status_modified_at, 
                    thread.status_modified_by, 
                    thread.deleted_at,
                    replies
        """

        count_query = f"""
            MATCH (topic:CommentTopic)<-[:TOPIC]-(thread: CommentThread)
            WHERE thread.is_deleted = false 
            {topic_clause}
            {status_clause}
            RETURN COUNT(thread) as total
        """

        try:
            result_array, attributes_names = db.cypher_query(
                query=full_query, params=params
            )

            threads_ars: list[CommentThreadAR] = []
            items = [dict(zip(attributes_names, res)) for res in result_array]
            for item in items:
                reply_ars = [
                    CommentReplyAR.from_repository_values(
                        uid=reply["uid"],
                        text=reply["text"],
                        author_id=reply["author_id"],
                        author_display_name=reply["author_display_name"],
                        comment_thread_uid=item["thread.uid"],
                        created_at=convert_to_datetime(reply["created_at"]),
                        modified_at=convert_to_datetime(reply.get("modified_at", None)),
                        deleted_at=convert_to_datetime(reply.get("deleted_at", None)),
                    )
                    for reply in item["replies"]
                ]
                reply_ars.sort(key=lambda x: x.created_at)

                threads_ars.append(
                    CommentThreadAR.from_repository_values(
                        uid=item["thread.uid"],
                        text=item["thread.text"],
                        author_id=item["thread.author_id"],
                        author_display_name=item["thread_author_display_name"],
                        status=item["thread.status"],
                        created_at=convert_to_datetime(item["thread.created_at"]),
                        modified_at=convert_to_datetime(item["thread.modified_at"]),
                        status_modified_at=convert_to_datetime(
                            item["thread.status_modified_at"]
                        ),
                        status_modified_by=item["thread.status_modified_by"],
                        deleted_at=convert_to_datetime(item["thread.deleted_at"]),
                        topic_path=item["topic.topic_path"],
                        replies=reply_ars,
                    )
                )

            count_result, _ = db.cypher_query(query=count_query, params=params)
            total_amount = count_result[0][0] if len(count_result) > 0 else 0

            return threads_ars, total_amount

        except CypherSyntaxError as ex:
            log.error("%s: %s", ex.code, ex.message)
            raise exceptions.ValidationException(
                msg="Unsupported filtering or sort parameters specified"
            ) from ex

    def find_all_comment_topics(
        self,
        topic_path: str | None = None,
        topic_path_partial_match: bool = False,
        page_number: int = 1,
        page_size: int = 0,
    ) -> tuple[list[CommentTopicAR], int]:
        validate_max_skip_clause(page_number=page_number, page_size=page_size)
        params = {
            "topic_path": topic_path,
            "skip": (page_number - 1) * page_size,
            "limit": page_size,
        }

        topic_clause = ""
        if topic_path is not None:
            if topic_path_partial_match:
                topic_clause = (
                    "AND toLower(topic.topic_path) CONTAINS toLower($topic_path) "
                )
            else:
                topic_clause = "AND toLower(topic.topic_path) = toLower($topic_path) "

        full_query = f"""
            MATCH (topic:CommentTopic)<-[:TOPIC]-(thread:CommentThread)
            WHERE thread.is_deleted = false 
            {topic_clause}
            WITH thread, topic
            ORDER BY topic.topic_path ASC
            WITH    topic.uid as topic_uid, 
                    topic.topic_path  as topic_path, 
                    thread.status as thread_status, 
                    count(thread) AS threads_count
            WITH    topic_uid, 
                    topic_path, 
                    collect(thread_status) as thread_statuses, 
                    collect(threads_count) as thread_counts
            SKIP $skip LIMIT $limit
            RETURN *
        """

        count_query = f"""
            MATCH (topic:CommentTopic)<-[:TOPIC]-(thread: CommentThread)
            WHERE thread.is_deleted = false 
            {topic_clause}
            RETURN COUNT(DISTINCT topic.uid) as total
        """

        try:
            result_array, attributes_names = db.cypher_query(
                query=full_query, params=params
            )

            topics_ars: list[CommentTopicAR] = []
            items = [dict(zip(attributes_names, res)) for res in result_array]
            for item in items:
                active_count = 0
                resolved_count = 0
                for idx, status in enumerate(item["thread_statuses"]):
                    if status == CommentThreadStatus.ACTIVE.value:
                        active_count = item["thread_counts"][idx]
                    elif status == CommentThreadStatus.RESOLVED.value:
                        resolved_count = item["thread_counts"][idx]

                topics_ars.append(
                    CommentTopicAR.from_repository_values(
                        uid=item["topic_uid"],
                        topic_path=item["topic_path"],
                        threads_active_count=active_count,
                        threads_resolved_count=resolved_count,
                    )
                )

            count_result, _ = db.cypher_query(query=count_query, params=params)
            total_amount = count_result[0][0] if len(count_result) > 0 else 0

            return topics_ars, total_amount

        except CypherSyntaxError as ex:
            log.error("%s: %s", ex.code, ex.message)
            raise exceptions.ValidationException(
                msg="Unsupported filtering or sort parameters specified"
            ) from ex

    def find_all_comment_thread_replies(
        self, thread_uid: str
    ) -> Collection[CommentReplyAR]:
        items: list[CommentReply] = CommentReply.nodes.filter(
            is_deleted=False, reply_to__uid=thread_uid, reply_to__is_deleted=False
        )
        item_ars: list[CommentReplyAR] = [
            CommentReplyAR.from_repository_values(
                uid=p[0].uid,
                text=p[0].text,
                author_id=p[0].author_id,
                author_display_name=UserInfoService.get_author_name_from_id(
                    p[0].author_id
                ),
                comment_thread_uid=thread_uid,
                created_at=p[0].created_at,
                modified_at=p[0].modified_at,
                deleted_at=p[0].deleted_at,
            )
            for p in items
        ]

        # attaching a proper repository closure data
        repository_closure_data = RepositoryClosureData(
            not_for_update=True, repository=self, additional_closure=None
        )
        for item_ar in item_ars:
            item_ar.repository_closure_data = repository_closure_data

        return item_ars

    @sb_clear_cache(caches=["cache_store_item_by_uid"])
    def delete_comment_thread(self, uid: str):
        node = CommentThread.nodes.first_or_none(uid=uid)
        if node is not None:
            node.is_deleted = True
            node.deleted_at = datetime.now()
            node.save()

    @sb_clear_cache(caches=["cache_store_item_by_uid"])
    def delete_comment_reply(self, uid: str):
        node = CommentReply.nodes.first_or_none(uid=uid)
        if node is not None:
            node.is_deleted = True
            node.deleted_at = datetime.now()
            node.save()

    def close(self) -> None:
        # Our repository guidelines state that repos should have a close method
        # But nothing needs to be done in this one
        pass
