from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable


class CommentThreadStatus(Enum):
    """
    Possible comment thread statuses
    """

    ACTIVE = "ACTIVE"
    RESOLVED = "RESOLVED"


@dataclass
class CommentReplyAR:
    repository_closure_data: Any = field(
        init=False, compare=False, repr=True, default=None
    )

    _uid: str
    comment_thread_uid: str
    text: str
    author_id: str
    author_display_name: str
    created_at: datetime
    modified_at: datetime | None = None
    deleted_at: datetime | None = None

    @property
    def uid(self) -> str:
        return self._uid

    @staticmethod
    def from_input_values(
        generate_uid_callback: Callable[[], str],
        text: str,
        author_id: str,
        author_display_name: str,
        comment_thread_uid: str,
        created_at: datetime,
        modified_at: datetime | None = None,
    ):
        uid = generate_uid_callback()

        return CommentReplyAR(
            _uid=uid,
            text=text,
            comment_thread_uid=comment_thread_uid,
            author_id=author_id,
            author_display_name=author_display_name,
            created_at=created_at,
            modified_at=modified_at,
        )

    @staticmethod
    def from_repository_values(
        uid: str,
        comment_thread_uid: str,
        text: str,
        author_id: str,
        author_display_name: str,
        created_at: datetime,
        modified_at: datetime | None = None,
        deleted_at: datetime | None = None,
    ):
        return CommentReplyAR(
            _uid=uid,
            comment_thread_uid=comment_thread_uid,
            text=text,
            author_id=author_id,
            author_display_name=author_display_name,
            created_at=created_at,
            modified_at=modified_at,
            deleted_at=deleted_at,
        )


@dataclass
class CommentThreadAR:
    repository_closure_data: Any = field(
        init=False, compare=False, repr=True, default=None
    )

    _uid: str
    text: str
    topic_path: str
    status: CommentThreadStatus
    author_id: str
    author_display_name: str
    created_at: datetime
    modified_at: datetime | None = None
    status_modified_at: datetime | None = None
    status_modified_by: str | None = None
    deleted_at: datetime | None = None
    replies: list[CommentReplyAR] = field(default_factory=list)

    @property
    def uid(self) -> str:
        return self._uid

    @staticmethod
    def from_input_values(
        generate_uid_callback: Callable[[], str],
        text: str,
        topic_path: str,
        author_id: str,
        author_display_name: str,
        status: CommentThreadStatus,
        created_at: datetime,
        modified_at: datetime | None = None,
        status_modified_at: datetime | None = None,
        status_modified_by: str | None = None,
    ):
        uid = generate_uid_callback()

        return CommentThreadAR(
            _uid=uid,
            text=text,
            topic_path=topic_path,
            author_id=author_id,
            author_display_name=author_display_name,
            status=status,
            created_at=created_at,
            modified_at=modified_at,
            status_modified_at=status_modified_at,
            status_modified_by=status_modified_by,
        )

    @staticmethod
    def from_repository_values(
        uid: str,
        text: str,
        topic_path: str,
        author_id: str,
        author_display_name: str,
        status: str,
        created_at: datetime,
        modified_at: datetime | None = None,
        status_modified_at: datetime | None = None,
        status_modified_by: str | None = None,
        deleted_at: datetime | None = None,
        replies: list[CommentReplyAR] | None = None,
    ):
        return CommentThreadAR(
            _uid=uid,
            text=text,
            topic_path=topic_path,
            author_id=author_id,
            author_display_name=author_display_name,
            status=CommentThreadStatus(status),
            created_at=created_at,
            modified_at=modified_at,
            status_modified_at=status_modified_at,
            status_modified_by=status_modified_by,
            deleted_at=deleted_at,
            replies=replies or [],
        )


@dataclass
class CommentTopicAR:
    repository_closure_data: Any = field(
        init=False, compare=False, repr=True, default=None
    )

    _uid: str
    topic_path: str
    threads_active_count: int = 0
    threads_resolved_count: int = 0

    @property
    def uid(self) -> str:
        return self._uid

    @staticmethod
    def from_input_values(
        generate_uid_callback: Callable[[], str],
        topic_path: str,
    ):
        uid = generate_uid_callback()

        return CommentTopicAR(
            _uid=uid,
            topic_path=topic_path,
        )

    @staticmethod
    def from_repository_values(
        uid: str,
        topic_path: str,
        threads_active_count: int = 0,
        threads_resolved_count: int = 0,
    ):
        return CommentTopicAR(
            _uid=uid,
            topic_path=topic_path,
            threads_active_count=threads_active_count,
            threads_resolved_count=threads_resolved_count,
        )
