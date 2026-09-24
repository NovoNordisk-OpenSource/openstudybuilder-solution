from clinical_mdr_api.domains.concepts.simple_concepts.simple_concept import (
    SimpleConceptAR,
    SimpleConceptVO,
)


class TextValueVO(SimpleConceptVO):
    pass


class TextValueAR(SimpleConceptAR):
    _concept_vo: TextValueVO

    @property
    def concept_vo(self) -> TextValueVO:
        return self._concept_vo
