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
        # if ID was already generated for the instance
        if (
            original_sb_id is not None
            and self._associated_ids.get(original_sb_id, None) is not None
        ):
            return self._associated_ids[original_sb_id]
        entity_number = self._ids[entity_class]
        self._ids[entity_class] += 1
        generated_id = f"{entity_class}_{entity_number + 1}"
        # if generated ID can be set in cache for other cases when an ID referring to an already generated ID is needed
        if original_sb_id is not None:
            self._associated_ids[original_sb_id] = generated_id
        return generated_id
