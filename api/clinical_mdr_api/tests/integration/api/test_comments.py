"""
Tests for /comment* endpoints
"""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments
# import json
import logging
from functools import reduce
from typing import Any

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.main import app
from clinical_mdr_api.models.comments.comments import CommentReply, CommentThread
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.unit.domain.utils import AUTHOR_ID
from clinical_mdr_api.tests.utils.checks import assert_response_status_code
from common.utils import convert_to_datetime

log = logging.getLogger(__name__)

# Global variables shared between fixtures and tests
threads: list[CommentThread]
replies: list[CommentReply]


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    db_name = "comments.api"
    inject_and_clear_db(db_name)
    inject_base_data()

    global threads
    global replies

    threads = []
    replies = []

    for index in range(25):
        topic_path = f"/Topic/{index % 5}"
        thread = TestUtils.create_comment_thread(
            topic_path=topic_path, text=f"Thread {index}"
        )
        threads.append(thread)
        for index2 in range(3):
            reply = TestUtils.create_comment_thread_reply(
                thread_uid=thread.uid, text=f"Reply {index}.{index2}"
            )
            replies.append(reply)

    yield


TOPIC_FIELDS_ALL = [
    "uid",
    "topic_path",
    "threads_active_count",
    "threads_resolved_count",
]
TOPIC_FIELDS_NOT_NULL = [
    "uid",
    "topic_path",
    "threads_active_count",
    "threads_resolved_count",
]
THREAD_FIELDS_ALL = [
    "uid",
    "author_id",
    "author_display_name",
    "text",
    "created_at",
    "modified_at",
    "topic_path",
    "status",
    "status_modified_at",
    "status_modified_by",
    "replies",
]
THREAD_FIELDS_NOT_NULL = [
    "uid",
    "text",
    "author_id",
    "author_display_name",
    "created_at",
    "status",
    "topic_path",
    "replies",
]
REPLY_FIELDS_ALL = [
    "uid",
    "author_id",
    "author_display_name",
    "text",
    "created_at",
    "modified_at",
    "comment_thread_uid",
]
REPLY_FIELDS_NOT_NULL = [
    "uid",
    "text",
    "author_id",
    "author_display_name",
    "created_at",
    "comment_thread_uid",
]


@pytest.mark.parametrize(
    "page_size, page_number, topic_path, topic_path_partial_match, expected_result_len, expected_total",
    [
        # Total number of topics is 5
        pytest.param(None, None, None, None, 5, 5),
        pytest.param(3, 1, None, None, 3, 5),
        pytest.param(3, 2, None, None, 2, 5),
        pytest.param(10, 2, None, None, 0, 5),
        pytest.param(10, 1, "/Topic/1", None, 1, 1),
        pytest.param(10, 1, "/Topic/1", True, 1, 1),
        pytest.param(10, 1, "/Topic/1", False, 1, 1),
        pytest.param(10, 1, "xyz", None, 0, 0),
        pytest.param(10, 1, "xyz", False, 0, 0),
        pytest.param(10, 1, "xyz", True, 0, 0),
        pytest.param(10, 1, "to", None, 0, 0),
        pytest.param(10, 1, "to", True, 5, 5),
        pytest.param(10, 1, "to", False, 0, 0),
    ],
)
def test_get_comment_topics(
    api_client,
    page_size,
    page_number,
    topic_path,
    topic_path_partial_match,
    expected_result_len,
    expected_total,
):
    url = "/comment-topics"
    query_params = []
    if page_size:
        query_params.append(f"page_size={page_size}")
    if page_number:
        query_params.append(f"page_number={page_number}")
    if topic_path:
        query_params.append(f"topic_path={topic_path}")
    if topic_path_partial_match is not None:
        query_params.append(f"topic_path_partial_match={topic_path_partial_match}")

    if query_params:
        url = f"{url}?{'&'.join(query_params)}"

    log.info("GET %s", url)
    response = api_client.get(url)
    res = response.json()

    assert_response_status_code(response, 200)

    # Check fields included in the response
    assert list(res.keys()) == ["items", "total", "page", "size"]
    assert len(res["items"]) == expected_result_len
    assert res["total"] == expected_total
    assert res["page"] == (page_number if page_number else 1)
    assert res["size"] == (page_size if page_size else 10)

    for item in res["items"]:
        assert set(list(item.keys())) == set(TOPIC_FIELDS_ALL)
        for key in TOPIC_FIELDS_NOT_NULL:
            assert item[key] is not None

    # Assert that results are sorted by 'topic_path' ascending
    result_vals = list(map(lambda x: x["topic_path"], res["items"]))
    result_vals_sorted_locally = result_vals.copy()
    result_vals_sorted_locally.sort()
    assert result_vals == result_vals_sorted_locally


def test_get_comment_thread(api_client):
    response = api_client.get(f"/comment-threads/{threads[0].uid}")
    res = response.json()

    assert_response_status_code(response, 200)

    # Check fields included in the response
    assert set(res.keys()) == set(THREAD_FIELDS_ALL)
    for key in THREAD_FIELDS_NOT_NULL:
        assert res[key] is not None

    assert res["uid"] == threads[0].uid
    assert res["author_id"] == AUTHOR_ID
    assert res["author_display_name"] == "John Smith"
    assert res["text"] == "Thread 0"
    assert res["topic_path"] == "/Topic/0"
    assert res["status"] == "ACTIVE"
    assert res["modified_at"] is None
    for reply in res["replies"]:
        assert set(list(reply.keys())) == set(REPLY_FIELDS_ALL)
        for key in REPLY_FIELDS_NOT_NULL:
            assert reply[key] is not None

    TestUtils.assert_timestamp_is_in_utc_zone(res["created_at"])
    TestUtils.assert_timestamp_is_newer_than(res["created_at"], 60)


def test_get_comment_threads_pagination(api_client):
    results_paginated: dict[Any, Any] = {}
    for page_number in range(1, 4):
        url = f"/comment-threads?page_number={page_number}&page_size=10"
        response = api_client.get(url)
        res = response.json()
        res_names = list(map(lambda x: x["text"], res["items"]))
        results_paginated[page_number] = res_names
        log.info("Page %s: %s", page_number, res_names)

    log.info("All pages: %s", results_paginated)

    results_paginated_merged = list(
        set(
            list(
                reduce(lambda a, b: list(a) + list(b), list(results_paginated.values()))
            )
        )
    )
    log.info("All unique rows returned by pagination: %s", results_paginated_merged)

    res_all = api_client.get("/comment-threads?page_number=1&page_size=100").json()
    results_all_in_one_page = list(map(lambda x: x["text"], res_all["items"]))
    log.info("All rows in one page: %s", results_all_in_one_page)
    assert len(results_all_in_one_page) == len(results_paginated_merged)
    assert len(threads) <= len(results_paginated_merged)


@pytest.mark.parametrize(
    "page_size, page_number, topic_path, topic_path_partial_match, status, expected_result_len, expected_total",
    [
        # Total number of threads is 25
        pytest.param(None, None, None, None, None, 10, 25),
        pytest.param(3, 1, None, None, None, 3, 25),
        pytest.param(3, 2, None, None, None, 3, 25),
        pytest.param(10, 2, None, None, None, 10, 25),
        pytest.param(10, 3, None, None, None, 5, 25),
        pytest.param(10, 1, None, None, None, 10, 25),
        pytest.param(10, 1, "/Topic/0", None, None, 5, 5),
        pytest.param(10, 1, "/Topic/0", True, None, 5, 5),
        pytest.param(10, 1, "/Topic/0", False, None, 5, 5),
        pytest.param(10, 1, "/Topic", True, None, 10, 25),
        pytest.param(10, 1, "/Topic", False, None, 0, 0),
        pytest.param(10, 2, "/Topic/6", None, None, 0, 0),
        pytest.param(10, 1, "/Topic/1", None, "ACTIVE", 5, 5),
        pytest.param(10, 2, "/Topic/1", None, "ACTIVE", 0, 5),
        pytest.param(10, 1, None, None, "ACTIVE", 10, 25),
        pytest.param(10, 1, None, None, "RESOLVED", 0, 0),
        pytest.param(10, 1, "/Topic/non-existent", None, None, 0, 0),
    ],
)
def test_get_comment_threads(
    api_client,
    page_size,
    page_number,
    topic_path,
    topic_path_partial_match,
    status,
    expected_result_len,
    expected_total,
):
    url = "/comment-threads"
    query_params = []
    if page_size:
        query_params.append(f"page_size={page_size}")
    if page_number:
        query_params.append(f"page_number={page_number}")
    if topic_path:
        query_params.append(f"topic_path={topic_path}")
    if topic_path_partial_match is not None:
        query_params.append(f"topic_path_partial_match={topic_path_partial_match}")
    if status:
        query_params.append(f"status={status}")

    if query_params:
        url = f"{url}?{'&'.join(query_params)}"

    log.info("GET %s", url)
    response = api_client.get(url)
    res = response.json()

    assert_response_status_code(response, 200)

    # Check fields included in the response
    assert list(res.keys()) == ["items", "total", "page", "size"]
    assert len(res["items"]) == expected_result_len
    assert res["total"] == expected_total
    assert res["page"] == (page_number if page_number else 1)
    assert res["size"] == (page_size if page_size else 10)

    for item in res["items"]:
        assert set(list(item.keys())) == set(THREAD_FIELDS_ALL)
        for key in THREAD_FIELDS_NOT_NULL:
            assert item[key] is not None
        for reply in item["replies"]:
            assert set(list(reply.keys())) == set(REPLY_FIELDS_ALL)
            for key in REPLY_FIELDS_NOT_NULL:
                assert reply[key] is not None
        TestUtils.assert_timestamp_is_in_utc_zone(item["created_at"])
        TestUtils.assert_timestamp_is_newer_than(item["created_at"], 60)

    # Assert that results are sorted by 'created_at' ascending
    result_vals = list(map(lambda x: x["created_at"], res["items"]))
    result_vals_sorted_locally = result_vals.copy()
    result_vals_sorted_locally.sort()
    assert result_vals == result_vals_sorted_locally


def test_get_comment_thread_reply(api_client):
    response = api_client.get(
        f"/comment-threads/{threads[0].uid}/replies/{replies[0].uid}"
    )
    res = response.json()

    assert_response_status_code(response, 200)

    # Check fields included in the response
    assert set(res.keys()) == set(REPLY_FIELDS_ALL)
    for key in REPLY_FIELDS_NOT_NULL:
        assert res[key] is not None

    assert res["uid"] == replies[0].uid
    assert res["author_id"] == AUTHOR_ID
    assert res["author_display_name"] == "John Smith"
    assert res["text"] == "Reply 0.0"
    assert res["comment_thread_uid"] == threads[0].uid
    assert res["modified_at"] is None

    TestUtils.assert_timestamp_is_in_utc_zone(res["created_at"])
    TestUtils.assert_timestamp_is_newer_than(res["created_at"], 60)


def test_get_comment_thread_replies(api_client):
    response = api_client.get(f"/comment-threads/{threads[0].uid}/replies")
    res = response.json()

    assert_response_status_code(response, 200)
    assert len(res) == 3
    for item in res:
        assert set(list(item.keys())) == set(REPLY_FIELDS_ALL)
        for key in REPLY_FIELDS_NOT_NULL:
            assert item[key] is not None
        assert item["comment_thread_uid"] == threads[0].uid
        TestUtils.assert_timestamp_is_in_utc_zone(item["created_at"])
        TestUtils.assert_timestamp_is_newer_than(item["created_at"], 60)


def test_create_comment_thread_and_reply(api_client):
    # Create a thread
    response = api_client.post(
        "/comment-threads", json={"text": "Thread X", "topic_path": "/Topic/0"}
    )
    thread = response.json()
    assert_response_status_code(response, 201)

    # Check fields included in the response
    assert set(list(thread.keys())) == set(THREAD_FIELDS_ALL)
    for key in THREAD_FIELDS_NOT_NULL:
        assert thread[key] is not None

    assert thread["author_id"] == AUTHOR_ID
    assert thread["author_display_name"] == "John Smith"
    assert thread["text"] == "Thread X"
    assert thread["topic_path"] == "/Topic/0"
    assert thread["status"] == "ACTIVE"
    assert thread["modified_at"] is None

    TestUtils.assert_timestamp_is_in_utc_zone(thread["created_at"])
    TestUtils.assert_timestamp_is_newer_than(thread["created_at"], 60)

    # Create a reply
    response = api_client.post(
        f"/comment-threads/{thread['uid']}/replies", json={"text": "Reply X"}
    )
    reply = response.json()
    assert_response_status_code(response, 201)

    # Check fields included in the response
    assert set(list(reply.keys())) == set(REPLY_FIELDS_ALL)
    for key in REPLY_FIELDS_NOT_NULL:
        assert reply[key] is not None

    assert reply["author_id"] == AUTHOR_ID
    assert reply["author_display_name"] == "John Smith"
    assert reply["text"] == "Reply X"
    assert reply["comment_thread_uid"] == thread["uid"]
    assert reply["modified_at"] is None

    TestUtils.assert_timestamp_is_in_utc_zone(reply["created_at"])
    TestUtils.assert_timestamp_is_newer_than(reply["created_at"], 60)


def test_reply_and_set_thread_status(api_client):
    # Create a thread
    response = api_client.post(
        "/comment-threads", json={"text": "Thread X", "topic_path": "/Topic/0"}
    )
    thread = response.json()
    assert_response_status_code(response, 201)

    # Reply and resolve thread
    response = api_client.post(
        f"/comment-threads/{thread['uid']}/replies",
        json={"text": "Reply and resolve", "thread_status": "RESOLVED"},
    )
    reply = response.json()
    assert_response_status_code(response, 201)

    # Check fields included in the response
    assert set(list(reply.keys())) == set(REPLY_FIELDS_ALL)
    for key in REPLY_FIELDS_NOT_NULL:
        assert reply[key] is not None

    assert reply["author_id"] == AUTHOR_ID
    assert reply["author_display_name"] == "John Smith"
    assert reply["text"] == "Reply and resolve"
    assert reply["comment_thread_uid"] == thread["uid"]
    assert reply["modified_at"] is None

    TestUtils.assert_timestamp_is_in_utc_zone(reply["created_at"])
    TestUtils.assert_timestamp_is_newer_than(reply["created_at"], 60)

    response = api_client.get(f"/comment-threads/{thread['uid']}")
    thread_resolved = response.json()
    assert_response_status_code(response, 200)
    assert thread_resolved["status"] == "RESOLVED"
    assert thread_resolved["status_modified_at"] is not None
    assert thread_resolved["status_modified_by"] == AUTHOR_ID
    TestUtils.assert_timestamp_is_newer_than(thread_resolved["status_modified_at"], 60)

    # Reply and reactivate thread
    response = api_client.post(
        f"/comment-threads/{thread['uid']}/replies",
        json={"text": "Reply and reactivate", "thread_status": "ACTIVE"},
    )
    reply = response.json()
    assert_response_status_code(response, 201)

    # Check fields included in the response
    assert set(list(reply.keys())) == set(REPLY_FIELDS_ALL)
    for key in REPLY_FIELDS_NOT_NULL:
        assert reply[key] is not None

    assert reply["author_id"] == AUTHOR_ID
    assert reply["author_display_name"] == "John Smith"
    assert reply["text"] == "Reply and reactivate"
    assert reply["comment_thread_uid"] == thread["uid"]
    assert reply["modified_at"] is None

    TestUtils.assert_timestamp_is_in_utc_zone(reply["created_at"])
    TestUtils.assert_timestamp_is_newer_than(reply["created_at"], 60)

    response = api_client.get(f"/comment-threads/{thread['uid']}")
    thread_active = response.json()
    assert_response_status_code(response, 200)
    assert thread_active["status"] == "ACTIVE"
    assert thread_active["status_modified_at"] is not None
    assert thread_active["status_modified_by"] == AUTHOR_ID
    TestUtils.assert_timestamp_is_newer_than(thread_active["status_modified_at"], 60)
    TestUtils.assert_chronological_sequence(
        thread_resolved["status_modified_at"], thread_active["status_modified_at"]
    )


def test_edit_comment_thread(api_client):
    # Create a thread
    response = api_client.post(
        "/comment-threads", json={"text": "Version 1", "topic_path": "/Topic/0"}
    )
    thread_ver_1 = response.json()
    assert_response_status_code(response, 201)
    assert thread_ver_1["author_id"] == AUTHOR_ID
    assert thread_ver_1["author_display_name"] == "John Smith"
    assert thread_ver_1["text"] == "Version 1"
    assert thread_ver_1["topic_path"] == "/Topic/0"
    assert thread_ver_1["status"] == "ACTIVE"
    assert thread_ver_1["created_at"] is not None
    assert thread_ver_1["modified_at"] is None

    TestUtils.assert_timestamp_is_in_utc_zone(thread_ver_1["created_at"])
    TestUtils.assert_timestamp_is_newer_than(thread_ver_1["created_at"], 60)

    # Edit thread
    response = api_client.patch(
        f"/comment-threads/{thread_ver_1['uid']}", json={"text": "Version 2"}
    )
    thread_ver_2 = response.json()
    assert_response_status_code(response, 200)
    assert thread_ver_2["uid"] == thread_ver_1["uid"]
    assert thread_ver_2["author_id"] == AUTHOR_ID
    assert thread_ver_2["author_display_name"] == "John Smith"
    assert thread_ver_2["text"] == "Version 2"
    assert thread_ver_2["topic_path"] == "/Topic/0"
    assert thread_ver_2["status"] == "ACTIVE"
    assert thread_ver_2["created_at"] == thread_ver_1["created_at"]
    assert thread_ver_2["modified_at"] is not None

    TestUtils.assert_timestamp_is_in_utc_zone(thread_ver_1["created_at"])
    TestUtils.assert_timestamp_is_newer_than(thread_ver_1["created_at"], 60)
    TestUtils.assert_chronological_sequence(
        thread_ver_2["created_at"], thread_ver_2["modified_at"]
    )

    # Edit thread
    response = api_client.patch(
        f"/comment-threads/{thread_ver_1['uid']}",
        json={"text": "Version 3", "status": "RESOLVED"},
    )
    thread_ver_3 = response.json()
    assert_response_status_code(response, 200)
    assert thread_ver_3["uid"] == thread_ver_1["uid"]
    assert thread_ver_3["author_id"] == AUTHOR_ID
    assert thread_ver_3["author_display_name"] == "John Smith"
    assert thread_ver_3["text"] == "Version 3"
    assert thread_ver_3["topic_path"] == "/Topic/0"
    assert thread_ver_3["status"] == "RESOLVED"
    assert thread_ver_3["created_at"] == thread_ver_1["created_at"]
    assert thread_ver_3["modified_at"] is not None

    TestUtils.assert_chronological_sequence(
        thread_ver_3["created_at"], thread_ver_3["modified_at"]
    )
    TestUtils.assert_chronological_sequence(
        thread_ver_2["modified_at"], thread_ver_3["modified_at"]
    )

    # Get thread
    response = api_client.get(f"/comment-threads/{thread_ver_1['uid']}")
    thread_final = response.json()
    assert_response_status_code(response, 200)
    assert thread_final == thread_ver_3

    # Check CommentThreadVersion nodes in db
    query = """
        MATCH (th:CommentThread {uid: $thread_uid})-[:PREVIOUS_VERSION]->(thv:CommentThreadVersion) 
        WITH th, thv
        ORDER by thv.from_ts ASC
        RETURN th.uid, th.text, th.status, th.created_at, th.modified_at, thv.text, thv.status, thv.from_ts, thv.to_ts
    """
    result_array, attributes_names = db.cypher_query(
        query, params={"thread_uid": thread_ver_1["uid"]}
    )

    versions_in_db = [dict(zip(attributes_names, res)) for res in result_array]
    assert len(versions_in_db) == 2
    assert versions_in_db[0]["th.uid"] == thread_ver_1["uid"]
    assert versions_in_db[0]["thv.text"] == "Version 1"
    assert versions_in_db[0]["thv.status"] == "ACTIVE"
    assert convert_to_datetime(
        versions_in_db[0]["thv.from_ts"]
    ) == TestUtils.get_datetime(thread_final["created_at"])
    assert versions_in_db[0]["thv.to_ts"] == versions_in_db[1]["thv.from_ts"]

    assert versions_in_db[0]["thv.from_ts"] < versions_in_db[0]["thv.to_ts"]

    assert versions_in_db[1]["th.uid"] == thread_ver_1["uid"]
    assert versions_in_db[1]["thv.text"] == "Version 2"
    assert versions_in_db[1]["thv.status"] == "ACTIVE"
    assert convert_to_datetime(
        versions_in_db[1]["thv.to_ts"]
    ) == TestUtils.get_datetime(thread_final["modified_at"])


@pytest.mark.skip("Skip until proper test auth is implemented")
def test_edit_comment_thread_unauthorized(api_client):
    # Create a thread
    response = api_client.post(
        "/comment-threads", json={"text": "Version 1", "topic_path": "/Topic/0"}
    )
    thread_ver_1 = response.json()

    # Edit thread with another user
    response = api_client.patch(
        f"/comment-threads/{thread_ver_1['uid']}",
        json={"text": "Version 2"},
        headers={"X-Test-User-Id": "another-user"},
    )
    res = response.json()
    assert_response_status_code(response, 403)
    assert res["message"] == "Only the author can edit a comment thread."


def test_edit_comment_reply(api_client):
    # Create a thread
    response = api_client.post(
        "/comment-threads", json={"text": "Thread A", "topic_path": "/Topic/0"}
    )
    thread = response.json()

    # Create a reply
    response = api_client.post(
        f"/comment-threads/{thread['uid']}/replies", json={"text": "Version 1"}
    )
    reply_ver_1 = response.json()
    assert_response_status_code(response, 201)
    assert reply_ver_1["comment_thread_uid"] == thread["uid"]
    assert reply_ver_1["uid"] is not None
    assert reply_ver_1["author_id"] == AUTHOR_ID
    assert reply_ver_1["author_display_name"] == "John Smith"
    assert reply_ver_1["text"] == "Version 1"
    assert reply_ver_1["created_at"] is not None
    assert reply_ver_1["modified_at"] is None

    TestUtils.assert_timestamp_is_in_utc_zone(reply_ver_1["created_at"])
    TestUtils.assert_timestamp_is_newer_than(reply_ver_1["created_at"], 60)

    TestUtils.assert_timestamp_is_in_utc_zone(reply_ver_1["created_at"])
    TestUtils.assert_timestamp_is_newer_than(reply_ver_1["created_at"], 60)

    # Edit reply
    response = api_client.patch(
        f"/comment-threads/{thread['uid']}/replies/{reply_ver_1['uid']}",
        json={"text": "Version 2"},
    )
    reply_ver_2 = response.json()
    assert_response_status_code(response, 200)
    assert reply_ver_2["author_id"] == AUTHOR_ID
    assert reply_ver_2["author_display_name"] == "John Smith"
    assert reply_ver_2["text"] == "Version 2"
    assert reply_ver_1["comment_thread_uid"] == thread["uid"]
    assert reply_ver_2["uid"] == reply_ver_1["uid"]
    assert reply_ver_2["created_at"] == reply_ver_1["created_at"]
    assert reply_ver_2["modified_at"] is not None

    TestUtils.assert_timestamp_is_in_utc_zone(reply_ver_2["created_at"])
    TestUtils.assert_timestamp_is_newer_than(reply_ver_2["created_at"], 60)
    TestUtils.assert_chronological_sequence(
        reply_ver_2["created_at"], reply_ver_2["modified_at"]
    )

    # Edit reply
    response = api_client.patch(
        f"/comment-threads/{thread['uid']}/replies/{reply_ver_1['uid']}",
        json={"text": "Version 3"},
    )
    reply_ver_3 = response.json()
    assert_response_status_code(response, 200)
    assert reply_ver_3["author_id"] == AUTHOR_ID
    assert reply_ver_3["author_display_name"] == "John Smith"
    assert reply_ver_3["text"] == "Version 3"
    assert reply_ver_3["comment_thread_uid"] == thread["uid"]
    assert reply_ver_3["uid"] == reply_ver_1["uid"]
    assert reply_ver_3["created_at"] == reply_ver_1["created_at"]
    assert reply_ver_3["modified_at"] is not None

    TestUtils.assert_chronological_sequence(
        reply_ver_3["created_at"], reply_ver_3["modified_at"]
    )
    TestUtils.assert_chronological_sequence(
        reply_ver_2["modified_at"], reply_ver_3["modified_at"]
    )

    # Get reply
    response = api_client.get(
        f"/comment-threads/{thread['uid']}/replies/{reply_ver_1['uid']}",
    )
    reply_final = response.json()
    assert_response_status_code(response, 200)
    assert reply_final == reply_ver_3

    # Check CommentReplyVersion nodes in db
    query = """
        MATCH (r:CommentReply {uid: $reply_uid})-[:PREVIOUS_VERSION]->(rv:CommentReplyVersion) 
        WITH r, rv
        ORDER by rv.from_ts ASC
        RETURN r.uid, r.text, r.created_at, r.modified_at, rv.text, rv.from_ts, rv.to_ts
    """
    result_array, attributes_names = db.cypher_query(
        query, params={"reply_uid": reply_ver_1["uid"]}
    )

    versions_in_db = [dict(zip(attributes_names, res)) for res in result_array]
    assert len(versions_in_db) == 2
    assert versions_in_db[0]["r.uid"] == reply_ver_1["uid"]
    assert versions_in_db[0]["rv.text"] == "Version 1"
    assert convert_to_datetime(
        versions_in_db[0]["rv.from_ts"]
    ) == TestUtils.get_datetime(reply_final["created_at"])
    assert versions_in_db[0]["rv.to_ts"] == versions_in_db[1]["rv.from_ts"]

    assert versions_in_db[0]["rv.from_ts"] < versions_in_db[0]["rv.to_ts"]

    assert versions_in_db[1]["r.uid"] == reply_ver_1["uid"]
    assert versions_in_db[1]["rv.text"] == "Version 2"
    assert convert_to_datetime(versions_in_db[1]["rv.to_ts"]) == TestUtils.get_datetime(
        reply_final["modified_at"]
    )


@pytest.mark.skip("Skip until proper test auth is implemented")
def test_edit_comment_reply_unauthorized(api_client):
    # Create a thread
    response = api_client.post(
        "/comment-threads", json={"text": "Thread A", "topic_path": "/Topic/0"}
    )
    thread = response.json()

    # Create a reply
    response = api_client.post(
        f"/comment-threads/{thread['uid']}/replies", json={"text": "Version 1"}
    )
    reply_ver_1 = response.json()
    assert_response_status_code(response, 201)

    # Edit reply with another user
    response = api_client.patch(
        f"/comment-threads/{reply_ver_1['uid']}/replies/{reply_ver_1['uid']}",
        json={"text": "Version 2"},
        headers={"X-Test-User-Id": "another-user"},
    )
    res = response.json()
    assert_response_status_code(response, 403)
    assert res["message"] == "Only the author can edit a comment thread reply."


def test_delete_comment_reply(api_client):
    # Create a thread
    response = api_client.post(
        "/comment-threads", json={"text": "Thread A", "topic_path": "/Topic/0"}
    )
    thread = response.json()

    # Create a reply
    response = api_client.post(
        f"/comment-threads/{thread['uid']}/replies", json={"text": "Version 1"}
    )
    reply = response.json()
    assert_response_status_code(response, 201)

    response = api_client.delete(
        f"/comment-threads/{thread['uid']}/replies/{reply['uid']}"
    )
    assert_response_status_code(response, 204)

    response = api_client.get(
        f"/comment-threads/{thread['uid']}/replies/{reply['uid']}"
    )
    assert_response_status_code(response, 404)
    assert (
        response.json()["message"]
        == f"Comment Reply with UID '{reply['uid']}' doesn't exist."
    )


@pytest.mark.skip("Skip until proper test auth is implemented")
def test_delete_comment_reply_unauthorized(api_client):
    # Create a thread
    response = api_client.post(
        "/comment-threads", json={"text": "Thread A", "topic_path": "/Topic/0"}
    )
    thread = response.json()

    # Create a reply
    response = api_client.post(
        f"/comment-threads/{thread['uid']}/replies", json={"text": "Version 1"}
    )
    reply_ver_1 = response.json()
    assert_response_status_code(response, 201)

    # Delete reply with another user
    response = api_client.delete(
        f"/comment-threads/{reply_ver_1['uid']}/replies/{reply_ver_1['uid']}",
        headers={"X-Test-User-Id": "another-user"},
    )
    res = response.json()
    assert_response_status_code(response, 403)
    assert res["message"] == "Only the author can delete a comment reply."


def test_delete_comment_thread(api_client):
    # Create a thread
    response = api_client.post(
        "/comment-threads", json={"text": "Thread A", "topic_path": "/Topic/0"}
    )
    thread = response.json()

    response = api_client.delete(f"/comment-threads/{thread['uid']}")
    assert_response_status_code(response, 204)

    response = api_client.get(f"/comment-threads/{thread['uid']}")
    assert_response_status_code(response, 404)
    assert (
        response.json()["message"]
        == f"Comment Thread with UID '{thread['uid']}' doesn't exist."
    )


@pytest.mark.skip("Skip until proper test auth is implemented")
def test_delete_comment_thread_unauthorized(api_client):
    # Create a thread
    response = api_client.post(
        "/comment-threads", json={"text": "Version 1", "topic_path": "/Topic/0"}
    )
    thread_ver_1 = response.json()

    # Delete thread with another user
    response = api_client.delete(
        f"/comment-threads/{thread_ver_1['uid']}",
        headers={"X-Test-User-Id": "another-user"},
    )
    res = response.json()
    assert_response_status_code(response, 403)
    assert res["message"] == "Only the author can delete a comment thread."
