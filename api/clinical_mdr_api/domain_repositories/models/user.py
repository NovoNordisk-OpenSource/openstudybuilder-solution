from neomodel import RelationshipTo

from clinical_mdr_api.domain_repositories.models.generic import (
    ClinicalMdrNode,
    ZonedDateTimeProperty,
)
from clinical_mdr_api.domain_repositories.models.preferences import UserPreferences
from common.neomodel import StringProperty


class User(ClinicalMdrNode):
    user_id = StringProperty(unique_index=True)
    username = StringProperty()
    name = StringProperty()
    email = StringProperty()
    azp = StringProperty()
    oid = StringProperty()
    roles = StringProperty()
    created = ZonedDateTimeProperty()
    updated = ZonedDateTimeProperty()

    has_preferences = RelationshipTo(UserPreferences, "HAS_PREFERENCES")
