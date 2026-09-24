from typing import TYPE_CHECKING

from clinical_mdr_api.domain_repositories.user_repository import UserRepository
from clinical_mdr_api.models.user import UserInfo

if TYPE_CHECKING:
    from typing import ClassVar


class UserInfoService:
    instance: "ClassVar[UserInfoService]"
    repo: UserRepository

    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super(UserInfoService, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        self.repo = UserRepository()

    def get_user(self, user_id: str) -> UserInfo:
        return self.repo.get_user(user_id)

    def get_users(self, ids: list[str]) -> list[UserInfo]:
        return self.repo.get_users_by_ids(ids)

    def get_all_users(self) -> list[UserInfo]:
        return self.repo.get_all_users()

    @classmethod
    def get_author_username_from_id(cls, user_id: str) -> str:
        user = cls().repo.get_user(user_id)
        return user.username if user and user.username else user_id

    @classmethod
    def get_author_name_from_id(cls, user_id: str) -> str:
        user = cls().repo.get_user(user_id)
        return user.name if user and user.name else user_id
