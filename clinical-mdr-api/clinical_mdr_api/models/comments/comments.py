from datetime import datetime
from typing import Annotated, Callable, Self

from pydantic import Field

from clinical_mdr_api.domains.comments.comments import (
    CommentReplyAR,
    CommentThreadAR,
    CommentThreadStatus,
    CommentTopicAR,
)
from clinical_mdr_api.models.utils import BaseModel, PatchInputModel, PostInputModel


class CommentReply(BaseModel):
    uid: Annotated[str, Field(description="Unique id of comment reply")]
    comment_thread_uid: Annotated[
        str,
        Field(description="Unique id of comment thread that this comment replies to"),
    ]

    text: Annotated[str, Field()]
    author_id: Annotated[str, Field()]
    author_display_name: Annotated[str, Field()]
    created_at: Annotated[datetime, Field()]
    modified_at: Annotated[
        datetime | None, Field(json_schema_extra={"nullable": True})
    ] = None

    @classmethod
    def from_uid(
        cls,
        uid: str,
        find_by_uid: Callable[[str], CommentReplyAR | None],
    ) -> Self | None:
        item = None
        item_ar: CommentReplyAR = find_by_uid(uid)
        if item_ar is not None:
            item = CommentReply.from_ar(item_ar)
        return item

    @classmethod
    def from_ar(
        cls,
        comment_thread_ar: CommentReplyAR,
    ) -> Self:
        return CommentReply(
            uid=comment_thread_ar.uid,
            comment_thread_uid=comment_thread_ar.comment_thread_uid,
            text=comment_thread_ar.text,
            author_id=comment_thread_ar.author_id,
            author_display_name=comment_thread_ar.author_display_name,
            created_at=comment_thread_ar.created_at,
            modified_at=comment_thread_ar.modified_at,
        )


class CommentReplyCreateInput(PostInputModel):
    text: Annotated[str, Field(min_length=1)]
    thread_status: Annotated[
        CommentThreadStatus | None,
        Field(description="New comment thread status after reply"),
    ] = None


class CommentReplyEditInput(PatchInputModel):
    text: Annotated[
        str | None, Field(description="Updated reply text", min_length=1)
    ] = None


class CommentThread(BaseModel):
    uid: Annotated[str, Field(description="Unique id of comment thread")]

    text: Annotated[str, Field()]
    topic_path: Annotated[str, Field()]
    author_id: Annotated[str, Field()]
    author_display_name: Annotated[str, Field()]
    status: Annotated[CommentThreadStatus, Field()]
    created_at: Annotated[datetime, Field()]
    modified_at: Annotated[
        datetime | None, Field(json_schema_extra={"nullable": True})
    ] = None
    status_modified_at: Annotated[
        datetime | None, Field(json_schema_extra={"nullable": True})
    ] = None
    status_modified_by: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    replies: Annotated[list[CommentReply], Field()] = []

    @classmethod
    def from_uid(
        cls,
        uid: str,
        find_by_uid: Callable[[str], CommentThreadAR | None],
    ) -> Self | None:
        comment_thread = None
        comment_thread_ar: CommentThreadAR = find_by_uid(uid)
        if comment_thread_ar is not None:
            comment_thread = CommentThread.from_ar(comment_thread_ar)
        return comment_thread

    @classmethod
    def from_ar(
        cls,
        comment_thread_ar: CommentThreadAR,
    ) -> Self:
        return CommentThread(
            uid=comment_thread_ar.uid,
            text=comment_thread_ar.text,
            topic_path=comment_thread_ar.topic_path,
            status=comment_thread_ar.status,
            author_id=comment_thread_ar.author_id,
            author_display_name=comment_thread_ar.author_display_name,
            created_at=comment_thread_ar.created_at,
            modified_at=comment_thread_ar.modified_at,
            status_modified_at=comment_thread_ar.status_modified_at,
            status_modified_by=comment_thread_ar.status_modified_by,
            replies=[
                CommentReply.from_ar(reply_ar) for reply_ar in comment_thread_ar.replies
            ],
        )


class CommentThreadCreateInput(PostInputModel):
    text: Annotated[str, Field(min_length=1)]
    topic_path: Annotated[str, Field(min_length=1)]


class CommentThreadEditInput(PatchInputModel):
    text: Annotated[
        str | None, Field(description="Updated thread text", min_length=1)
    ] = None
    status: Annotated[
        CommentThreadStatus | None, Field(description="Updated thread status")
    ] = None


class CommentTopic(BaseModel):
    uid: Annotated[str, Field(description="Unique id of comment topic")]

    topic_path: Annotated[str, Field()]
    threads_active_count: Annotated[int, Field()]
    threads_resolved_count: Annotated[int, Field()]

    @classmethod
    def from_uid(
        cls,
        uid: str,
        find_by_uid: Callable[[str], CommentThreadAR | None],
    ) -> Self | None:
        comment_thread = None
        comment_thread_ar: CommentThreadAR = find_by_uid(uid)
        if comment_thread_ar is not None:
            comment_thread = CommentThread.from_ar(comment_thread_ar)
        return comment_thread

    @classmethod
    def from_ar(
        cls,
        comment_topic_ar: CommentTopicAR,
    ) -> Self:
        return CommentTopic(
            uid=comment_topic_ar.uid,
            topic_path=comment_topic_ar.topic_path,
            threads_active_count=comment_topic_ar.threads_active_count,
            threads_resolved_count=comment_topic_ar.threads_resolved_count,
        )
