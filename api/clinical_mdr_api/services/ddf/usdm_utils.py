from collections import defaultdict


class IdManager:
    def __init__(self):
        self._ids = defaultdict(int)
        self._associated_ids = {}

    def clear_all_ids(self) -> None:
        self._ids = defaultdict(int)

    def clear_entity_id(self, entity_class) -> None:
        self._ids[entity_class] = 0

    def get_id(self, entity_class: str, original_sb_id: str | None = None) -> str:
        cache_key = (
            (entity_class, original_sb_id) if original_sb_id is not None else None
        )
        if cache_key is not None and cache_key in self._associated_ids:
            return self._associated_ids[cache_key]
        entity_number = self._ids[entity_class]
        self._ids[entity_class] += 1
        generated_id = f"{entity_class}_{entity_number + 1}"
        if cache_key is not None:
            self._associated_ids[cache_key] = generated_id
        return generated_id
