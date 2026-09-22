from neomodel import One, RelationshipFrom, RelationshipTo, ZeroOrMore

from clinical_mdr_api.domain_repositories.models.generic import (
    ClinicalMdrNodeWithUID,
    ClinicalMdrRel,
    ZonedDateTimeProperty,
)
from common.neomodel import BooleanProperty, StringProperty


class CommentTopic(ClinicalMdrNodeWithUID):
    topic_path = StringProperty()

    threads = RelationshipFrom(
        "CommentThread",
        "TOPIC",
        cardinality=ZeroOrMore,
        model=ClinicalMdrRel,
    )


class CommentThread(ClinicalMdrNodeWithUID):
    text = StringProperty()
    author_id = StringProperty()
    status = StringProperty()
    created_at = ZonedDateTimeProperty()
    modified_at = ZonedDateTimeProperty()
    status_modified_at = ZonedDateTimeProperty()
    status_modified_by = StringProperty()
    deleted_at = ZonedDateTimeProperty()
    is_deleted = BooleanProperty(default=False)

    topic = RelationshipTo(
        CommentTopic,
        "TOPIC",
        cardinality=One,
        model=ClinicalMdrRel,
    )

    previous_version = RelationshipTo(
        "CommentThreadVersion",
        "PREVIOUS_VERSION",
        cardinality=ZeroOrMore,
        model=ClinicalMdrRel,
    )

    replies = RelationshipFrom(
        "CommentReply",
        "REPLY_TO",
        cardinality=ZeroOrMore,
        model=ClinicalMdrRel,
    )


class CommentThreadVersion(ClinicalMdrNodeWithUID):
    text = StringProperty()
    status = StringProperty()
    status_modified_at = ZonedDateTimeProperty()
    status_modified_by = StringProperty()
    from_ts = ZonedDateTimeProperty()
    to_ts = ZonedDateTimeProperty()

    version_of = RelationshipFrom(
        CommentThread,
        "PREVIOUS_VERSION",
        cardinality=One,
        model=ClinicalMdrRel,
    )


class CommentReply(ClinicalMdrNodeWithUID):
    text = StringProperty()
    author_id = StringProperty()
    created_at = ZonedDateTimeProperty()
    modified_at = ZonedDateTimeProperty()
    deleted_at = ZonedDateTimeProperty()
    is_deleted = BooleanProperty(default=False)

    reply_to = RelationshipTo(
        CommentThread,
        "REPLY_TO",
        cardinality=One,
        model=ClinicalMdrRel,
    )

    previous_version = RelationshipTo(
        "CommentReplyVersion",
        "PREVIOUS_VERSION",
        cardinality=ZeroOrMore,
        model=ClinicalMdrRel,
    )


class CommentReplyVersion(ClinicalMdrNodeWithUID):
    text = StringProperty()
    from_ts = ZonedDateTimeProperty()
    to_ts = ZonedDateTimeProperty()

    version_of = RelationshipFrom(
        CommentReply,
        "PREVIOUS_VERSION",
        cardinality=One,
        model=ClinicalMdrRel,
    )
