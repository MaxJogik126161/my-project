from dataclasses import dataclass, field

@dataclass
class UserData:
    user_id: int
    full_name: str
    username: str | None

@dataclass
class UserStorage:
    _users: dict[int, UserData] = field(default_factory=dict)

    def add(
        self,
        user_id: int,
        full_name: str,
        username: str | None = None
    ) -> None:
        self._users[user_id] = UserData(
            user_id=user_id,
            full_name=full_name,
            username=username
        )

    def all(self) -> list[UserData]:
        return list(self._users.values())

    def all_ids(self) -> set[int]:
        return set(self._users.keys())

    def count(self) -> int:
        return len(self._users)

    def get_page(
        self,
        page: int,
        page_size: int = 10
    ) -> list[UserData]:
        users = self.all()
        start = page * page_size
        end = start + page_size
        return users[start:end]

    def total_pages(self, page_size: int = 10) -> int:
        if self.count() == 0:
            return 1
        return (self.count() + page_size - 1) // page_size

    def __contains__(self, user_id: int) -> bool:
        return user_id in self._users

user_storage = UserStorage()
