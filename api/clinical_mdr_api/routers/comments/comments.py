from typing import Annotated

from fastapi import APIRouter, Body, Path, Query

from clinical_mdr_api.domains.comments.comments import CommentThreadStatus
from clinical_mdr_api.models.comments.comments import (
    CommentReply,
    CommentReplyCreateInput,
    CommentReplyEditInput,
    CommentThread,
    CommentThreadCreateInput,
    CommentThreadEditInput,
    CommentTopic,
)
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.routers import _generic_descriptions
from clinical_mdr_api.services.comments.comments import CommentsService
from common.auth import rbac
from common.auth.dependencies import security
from common.config import settings

# Endpoints prefixed with "/comment*"
router = APIRouter()

CommentThreadUID = Path(description="Unique id of comment thread")
CommentReplyUID = Path(description="Unique id of comment reply")
Service = CommentsService


@router.get(
    "/comment-topics",
    dependencies=[security, rbac.ANY],
    summary="Returns all comment topics",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
    },
)
# pylint: disable=redefined-outer-name
def get_comment_topics(
    topic_path: Annotated[
        str | None,
        Query(
            min_length=1,
            description="If specified, only topic matching the specified value are returned.",
        ),
    ] = None,
    topic_path_partial_match: Annotated[
        bool,
        _generic_descriptions.STRICT_BOOL_VALIDATOR,
        Query(
            description="""If `false`, only topics whose topic path is equal to the specified `topic_path` are returned.
        If `true`, topics whose topic path partially matches the specified `topic_path` are returned.""",
        ),
    ] = False,
    page_number: _generic_descriptions.PAGE_NUMBER_QUERY = settings.default_page_number,
    page_size: _generic_descriptions.PAGE_SIZE_QUERY = settings.default_page_size,
) -> CustomPage[CommentTopic]:
    results = Service().get_all_comment_topics(
        topic_path=topic_path,
        topic_path_partial_match=topic_path_partial_match,
        page_number=page_number,
        page_size=page_size,
    )
    return CustomPage(
        items=results.items, total=results.total, page=page_number, size=page_size
    )


@router.get(
    "/comment-threads",
    dependencies=[security, rbac.ANY],
    summary="Returns all comment threads",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
    },
)
# pylint: disable=redefined-outer-name
def get_comment_threads(
    topic_path: Annotated[
        str | None,
        Query(
            min_length=1,
            description="The topic path of the comment thread. If not specified, comment threads associated with any topic are returned.",
        ),
    ] = None,
    topic_path_partial_match: Annotated[
        bool,
        _generic_descriptions.STRICT_BOOL_VALIDATOR,
        Query(
            description="""If `false`, only comment threads whose topic path is equal to the specified `topic_path` are returned.
        If `true`, comment threads whose topic path partially matches the specified `topic_path` are returned.""",
        ),
    ] = False,
    status: Annotated[
        CommentThreadStatus | None,
        Query(
            description="The status of the comment thread. If not specified, comment threads with any status are returned.",
        ),
    ] = None,
    page_number: _generic_descriptions.PAGE_NUMBER_QUERY = settings.default_page_number,
    page_size: _generic_descriptions.PAGE_SIZE_QUERY = settings.default_page_size,
) -> CustomPage[CommentThread]:
    results = Service().get_all_comment_threads(
        topic_path=topic_path,
        topic_path_partial_match=topic_path_partial_match,
        status=status,
        page_number=page_number,
        page_size=page_size,
    )
    return CustomPage(
        items=results.items, total=results.total, page=page_number, size=page_size
    )


@router.get(
    "/comment-threads/{comment_thread_uid}",
    dependencies=[security, rbac.ANY],
    summary="Returns the comment thread identified by the specified 'comment_thread_uid'.",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_comment_thread(
    comment_thread_uid: Annotated[str, CommentThreadUID],
) -> CommentThread:
    return Service().get_comment_thread(comment_thread_uid)


@router.post(
    "/comment-threads",
    dependencies=[security, rbac.ANY],
    summary="Creates a new comment thread",
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "Comment thread was successfully created"},
    },
)
def create_comment_thread(
    create_input: Annotated[
        CommentThreadCreateInput,
        Body(description="Comment thread that shall be created"),
    ],
) -> CommentThread:
    return Service().create_comment_thread(create_input)


@router.patch(
    "/comment-threads/{comment_thread_uid}",
    dependencies=[security, rbac.ANY],
    summary="Edits a comment thread's 'text' and/or 'status' properties",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "Comment thread was successfully edited"},
        404: _generic_descriptions.ERROR_404,
    },
)
def edit_comment_thread(
    comment_thread_uid: Annotated[str, CommentThreadUID],
    edit_input: Annotated[
        CommentThreadEditInput,
        Body(description="Properties of the comment thread that shall be updated"),
    ],
) -> CommentThread:
    return Service().edit_comment_thread(comment_thread_uid, edit_input)


@router.delete(
    "/comment-threads/{comment_thread_uid}",
    dependencies=[security, rbac.ANY],
    summary="Deletes the comment thread identified by 'comment_thread_uid'.",
    status_code=204,
    responses={
        403: _generic_descriptions.ERROR_403,
        204: {"description": "No Content - The item was successfully deleted."},
    },
)
def delete_comment_thread(comment_thread_uid: Annotated[str, CommentThreadUID]):
    Service().delete_comment_thread(comment_thread_uid)


@router.post(
    "/comment-threads/{comment_thread_uid}/replies",
    dependencies=[security, rbac.ANY],
    summary="Creates a reply to a comment thread",
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "Reply was successfully created"},
        404: _generic_descriptions.ERROR_404,
    },
)
def create_comment_reply(
    comment_thread_uid: Annotated[str, CommentThreadUID],
    create_input: Annotated[
        CommentReplyCreateInput, Body(description="Comment reply that shall be created")
    ],
) -> CommentReply:
    return Service().create_comment_reply(comment_thread_uid, create_input)


@router.get(
    "/comment-threads/{comment_thread_uid}/replies",
    dependencies=[security, rbac.ANY],
    summary="Returns all replies to the specified comment thread",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_comment_thread_replies(
    comment_thread_uid: Annotated[str, CommentThreadUID],
) -> list[CommentReply]:
    return Service().get_all_comment_thread_replies(comment_thread_uid)


@router.get(
    "/comment-threads/{comment_thread_uid}/replies/{reply_uid}",
    dependencies=[security, rbac.ANY],
    summary="Returns the comment thread reply identified by the specified 'reply_uid'.",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
# pylint: disable=unused-argument
def get_comment_thread_reply(
    comment_thread_uid: Annotated[str, CommentThreadUID],
    reply_uid: Annotated[str, CommentReplyUID],
) -> CommentReply:
    return Service().get_comment_thread_reply(reply_uid)


@router.patch(
    "/comment-threads/{comment_thread_uid}/replies/{reply_uid}",
    dependencies=[security, rbac.ANY],
    summary="Edits the specified comment reply's text",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "Comment reply was successfully edited"},
        404: _generic_descriptions.ERROR_404,
    },
)
# pylint: disable=unused-argument
def edit_comment_thread_reply(
    comment_thread_uid: Annotated[str, CommentThreadUID],
    reply_uid: Annotated[str, CommentReplyUID],
    edit_input: Annotated[
        CommentReplyEditInput, Body(description="Updated text of the comment reply")
    ],
) -> CommentReply:
    return Service().edit_comment_thread_reply(reply_uid, edit_input)


@router.delete(
    "/comment-threads/{comment_thread_uid}/replies/{reply_uid}",
    dependencies=[security, rbac.ANY],
    summary="Deletes the comment reply identified by 'reply_uid'.",
    status_code=204,
    responses={
        403: _generic_descriptions.ERROR_403,
        204: {"description": "No Content - The item was successfully deleted."},
    },
)
# pylint: disable=unused-argument
def delete_comment_reply(
    comment_thread_uid: Annotated[str, CommentThreadUID],
    reply_uid: Annotated[str, CommentReplyUID],
):
    Service().delete_comment_reply(reply_uid)
