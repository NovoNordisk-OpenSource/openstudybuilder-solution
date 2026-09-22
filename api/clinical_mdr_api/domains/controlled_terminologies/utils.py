from enum import Enum
from typing import Self


class TermParentType(Enum):
    """
    Enum for Type of has_parent relationship
    """

    PARENT_TYPE = "type"
    PARENT_SUB_TYPE = "subtype"
    SPECIALIZATION = "specialization"
    PREDECESSOR = "predecessor"


class CtTermInfo:
    def __init__(self, term_uid: str | None, name: str | None):
        self.term_uid = term_uid
        self.name = name

    @classmethod
    def extract_ct_term_info(cls, ct_term_context) -> Self:
        """Extract CtTermInfo object for a given CtTermContext node in the db"""
        ct_term_info = None

        if ct_term_context is not None:
            if ct_term_root := ct_term_context.has_selected_term.get_or_none():
                ct_term_info = CtTermInfo(term_uid=ct_term_root.uid, name=None)
                if (
                    ct_term_name_val := ct_term_root.has_name_root.get().has_latest_value.get_or_none()
                ):
                    ct_term_info.name = ct_term_name_val.name
        return ct_term_info
