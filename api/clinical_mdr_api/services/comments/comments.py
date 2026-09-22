import copy
from datetime import datetime

from neomodel import db  # type: ignore

from clinical_mdr_api.domains.comments.comments import (
    CommentReplyAR,
    CommentThreadAR,
    CommentThreadStatus,
    CommentTopicAR,
)
from clinical_mdr_api.models.comments.comments import (
    CommentReply,
    CommentReplyCreateInput,
    CommentReplyEditInput,
    CommentThread,
    CommentThreadCreateInput,
    CommentThreadEditInput,
    CommentTopic,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.services._meta_repository import MetaRepository  # type: ignore
from common.auth.user import user
from common.exceptions import ForbiddenException, NotFoundException


class CommentsService:
    def __init__(self):
        self.user_info = user()
        self.repos = MetaRepository()

    def get_all_comment_topics(
        self,
        topic_path: str | None = None,
        topic_path_partial_match: bool = False,
        page_number: int = 1,
        page_size: int = 0,
    ) -> GenericFilteringReturn[CommentTopic]:
        try:
            item_ars, total = self.repos.comments_repository.find_all_comment_topics(
                topic_path=topic_path,
                topic_path_partial_match=topic_path_partial_match,
                page_number=page_number,
                page_size=page_size,
            )

            items = [CommentTopic.from_ar(item_ar) for item_ar in item_ars]
            return GenericFilteringReturn(items=items, total=total)
        finally:
            self.repos.close()

    def get_all_comment_threads(
        self,
        topic_path: str | None = None,
        topic_path_partial_match: bool = False,
        status: CommentThreadStatus | None = None,
        page_number: int = 1,
        page_size: int = 0,
    ) -> GenericFilteringReturn[CommentThread]:
        try:
            item_ars, total = self.repos.comments_repository.find_all_comment_threads(
                topic_path=topic_path,
                topic_path_partial_match=topic_path_partial_match,
                status=status,
                page_number=page_number,
                page_size=page_size,
            )

            items = [CommentThread.from_ar(item_ar) for item_ar in item_ars]
            return GenericFilteringReturn(items=items, total=total)
        finally:
            self.repos.close()

    def get_comment_thread(self, uid: str) -> CommentThread:
        repos = MetaRepository()
        try:
            comment_thread = CommentThread.from_uid(
                uid, repos.comments_repository.find_comment_thread_by_uid
            )
            NotFoundException.raise_if(comment_thread is None, "Comment Thread", uid)
            comment_thread.replies = [
                CommentReply.from_ar(reply_ar)
                for reply_ar in self.repos.comments_repository.find_all_comment_thread_replies(
                    uid
                )
            ]
            return comment_thread
        finally:
            self.repos.close()

    @db.transaction
    def create_comment_thread(
        self, comment_thread_create_input: CommentThreadCreateInput
    ) -> CommentThread:
        try:
            comment_thread_ar = CommentThreadAR.from_input_values(
                text=comment_thread_create_input.text,
                topic_path=comment_thread_create_input.topic_path,
                author_id=self.user_info.id(),
                author_display_name=self.user_info.name,
                status=CommentThreadStatus.ACTIVE,
                created_at=datetime.now(),
                generate_uid_callback=self.repos.comments_repository.generate_thread_uid,
            )

            # Retrieve existing topic or create one if not found
            comment_topic_ar = self.repos.comments_repository.find_topic_by_path(
                comment_thread_create_input.topic_path
            )
            if not comment_topic_ar:
                comment_topic_ar = CommentTopicAR.from_input_values(
                    topic_path=comment_thread_create_input.topic_path,
                    generate_uid_callback=self.repos.comments_repository.generate_topic_uid,
                )
                self.repos.comments_repository.save_comment_topic(comment_topic_ar)

            self.repos.comments_repository.save_comment_thread(comment_thread_ar)
            return CommentThread.from_uid(
                comment_thread_ar.uid,
                self.repos.comments_repository.find_comment_thread_by_uid,
            )
        finally:
            self.repos.close()

    def _edit_comment_thread(
        self, uid: str, comment_thread_edit_input: CommentThreadEditInput
    ) -> CommentThread:
        try:
            comment_thread_latest = (
                self.repos.comments_repository.find_comment_thread_by_uid(uid)
            )
            NotFoundException.raise_if(
                comment_thread_latest is None, "Comment Thread", uid
            )

            comment_thread_previous = copy.deepcopy(comment_thread_latest)

            if comment_thread_edit_input.text is not None:
                ForbiddenException.raise_if(
                    comment_thread_latest.author_id != self.user_info.id(),
                    msg="Only the author can edit a comment thread.",
                )
                comment_thread_latest.text = comment_thread_edit_input.text

            if comment_thread_edit_input.status is not None:
                comment_thread_latest.status = comment_thread_edit_input.status

            if comment_thread_previous != comment_thread_latest:
                self.repos.comments_repository.edit_comment_thread(
                    comment_thread_latest,
                    comment_thread_previous,
                    self.user_info.id(),
                )

            return CommentThread.from_uid(
                comment_thread_latest.uid,
                self.repos.comments_repository.find_comment_thread_by_uid,
            )
        finally:
            self.repos.close()

    @db.transaction
    def edit_comment_thread(
        self, uid: str, comment_thread_edit_input: CommentThreadEditInput
    ) -> CommentThread:
        return self._edit_comment_thread(uid, comment_thread_edit_input)

    @db.transaction
    def delete_comment_thread(self, uid: str):
        comment_thread = self.repos.comments_repository.find_comment_thread_by_uid(uid)
        ForbiddenException.raise_if(
            comment_thread and comment_thread.author_id != self.user_info.id(),
            msg="Only the author can delete a comment thread.",
        )
        self.repos.comments_repository.delete_comment_thread(uid)

    def get_all_comment_thread_replies(self, thread_uid: str) -> list[CommentReply]:
        try:
            all_items = self.repos.comments_repository.find_all_comment_thread_replies(
                thread_uid
            )
            self.repos.comments_repository.close()
            return [CommentReply.from_ar(item_ar) for item_ar in all_items]
        finally:
            self.repos.close()

    def get_comment_thread_reply(self, uid: str) -> CommentReply:
        repos = MetaRepository()
        try:
            item = CommentReply.from_uid(
                uid, repos.comments_repository.find_comment_reply_by_uid
            )
            NotFoundException.raise_if(item is None, "Comment Reply", uid)
            return item
        finally:
            self.repos.close()

    @db.transaction
    def create_comment_reply(
        self, thread_uid: str, create_input: CommentReplyCreateInput
    ) -> CommentReply:
        try:
            comment_reply_ar = CommentReplyAR.from_input_values(
                text=create_input.text,
                comment_thread_uid=thread_uid,
                author_id=self.user_info.id(),
                author_display_name=self.user_info.name,
                created_at=datetime.now(),
                generate_uid_callback=self.repos.comments_repository.generate_reply_uid,
            )

            # Validate that the comment thread exists
            NotFoundException.raise_if_not(
                self.repos.comments_repository.find_comment_thread_by_uid(thread_uid),
                "Comment Thread",
                thread_uid,
            )

            if create_input.thread_status:
                self._edit_comment_thread(
                    thread_uid,
                    CommentThreadEditInput(
                        status=create_input.thread_status,
                    ),
                )

            self.repos.comments_repository.save_comment_reply(comment_reply_ar)
            return CommentReply.from_uid(
                comment_reply_ar.uid,
                self.repos.comments_repository.find_comment_reply_by_uid,
            )
        finally:
            self.repos.close()

    @db.transaction
    def edit_comment_thread_reply(
        self, uid: str, reply_edit_input: CommentReplyEditInput
    ) -> CommentReply:
        try:
            reply_latest = self.repos.comments_repository.find_comment_reply_by_uid(uid)

            NotFoundException.raise_if(
                reply_latest is None, "Comment Thread Reply", uid
            )

            reply_previous = copy.deepcopy(reply_latest)

            if reply_edit_input.text != reply_latest.text:
                ForbiddenException.raise_if(
                    reply_latest.author_id != self.user_info.id(),
                    msg="Only the author can edit a comment thread reply.",
                )
                reply_latest.text = reply_edit_input.text

                self.repos.comments_repository.edit_comment_reply(
                    reply_latest, reply_previous
                )

            return CommentReply.from_uid(
                reply_latest.uid,
                self.repos.comments_repository.find_comment_reply_by_uid,
            )
        finally:
            self.repos.close()

    @db.transaction
    def delete_comment_reply(self, uid: str):
        comment_reply = self.repos.comments_repository.find_comment_reply_by_uid(uid)
        ForbiddenException.raise_if(
            comment_reply and comment_reply.author_id != self.user_info.id(),
            msg="Only the author can delete a comment reply.",
        )
        self.repos.comments_repository.delete_comment_reply(uid)
