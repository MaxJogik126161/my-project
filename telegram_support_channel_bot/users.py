from dataclasses import dataclass, field

@dataclass
class UserStorage:
    _users: set[int] = field(default_factory=set)

    def add(self, user_id: int) -> None:
        self._users.add(user_id)

    def all(self) -> set[int]:
        return self._users.copy()

    def count(self) -> int:
        return len(self._users)

    def __contains__(self, user_id: int) -> bool:
        return user_id in self._users

user_storage = UserStorage()
