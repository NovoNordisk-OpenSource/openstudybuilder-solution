from clinical_mdr_api.domains.concepts.simple_concepts.text_value import (
    TextValueAR,
    TextValueVO,
)


class VisitNameVO(TextValueVO):
    pass


class VisitNameAR(TextValueAR):
    _concept_vo: VisitNameVO

    @property
    def concept_vo(self) -> VisitNameVO:
        return self._concept_vo
