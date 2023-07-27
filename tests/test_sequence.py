"""Tests for `pydantic_collections.sequence` module."""
import json
import typing as t

import pydantic as pdt
import pytest

from pydantic_collections.core import CollectionModelConfig
from pydantic_collections.sequence import PydanticSequence


class User(pdt.BaseModel):
    """A user."""

    name: str
    age: int


class UsersSequence(PydanticSequence[User]):
    """A sequence of users."""

    def __init__(self, *data: User) -> None:
        """Initialize Users."""
        super().__init__(*data)


class WeakUsersSequence(PydanticSequence[User]):
    """A sequence of users with weak validation."""

    model_config = CollectionModelConfig(validate_assignment_strict=False)


class UserData(t.TypedDict):
    """Dict version of User."""

    name: str
    age: int


UsersData = list[UserData]
UsersSequenceData = list[User]


class HasUsersSequence(pdt.BaseModel):
    """A class with a PydanticSequence."""

    users: UsersSequence


@pytest.fixture()
def user_count() -> int:
    """Return number of users."""
    return 2


@pytest.fixture()
def users_data(user_count: int) -> UsersData:
    """Return data for multiple users."""
    return [dict(name=f"Name {i}", age=i) for i in range(user_count)]  # type: ignore


@pytest.fixture()
def users_sequence_data(users_data: UsersData) -> UsersSequenceData:
    """Return multiple users."""
    return [User(**data) for data in users_data]


@pytest.fixture()
def users(users_sequence_data: UsersSequenceData) -> UsersSequence:
    """Return a Users object."""
    return UsersSequence(*users_sequence_data)


@pytest.fixture()
def weak_users_sequence(users_sequence_data: UsersSequenceData) -> WeakUsersSequence:
    """Return a WeakUsersSequence object."""
    return WeakUsersSequence(*users_sequence_data)


class TestPydanticSequence:
    """Tests for `PydanticSequence`."""

    def test_length(self, users: UsersSequence, user_count: int) -> None:
        """I can get the length of a PydanticSequence."""
        assert len(users) == user_count

    def test_get_item(self, users: UsersSequence, users_data: UsersData) -> None:
        """I can get an item from a PydanticSequence by indexing it."""
        checked_once = False
        for i, user_data in enumerate(users_data):
            assert users[i] == User(**user_data)
            checked_once = True
        assert checked_once

    def test_model_dump(self, users: UsersSequence, users_data: UsersData) -> None:
        """I can get a dictionary representation of a PydanticSequence."""
        assert users.model_dump() == users_data

    def test_model_dump_json(self, users: UsersSequence, users_data: UsersData) -> None:
        """I can get a JSON representation of a PydanticSequence."""
        model_dump_json = users.model_dump_json()
        json_dumps = json.dumps(users_data)
        assert json.loads(model_dump_json) == json.loads(json_dumps)

    def test_model_validate(self, users: UsersSequence, users_data: UsersData) -> None:
        """I can validate a PydanticSequence."""
        assert UsersSequence.model_validate(users_data) == users

    def test_model_validate_json(
        self, users: UsersSequence, users_data: UsersData
    ) -> None:
        """I can validate a PydanticSequence from JSON."""
        assert UsersSequence.model_validate_json(json.dumps(users_data)) == users

    def test_in_place_sort(self, users: UsersSequence, users_data: UsersData) -> None:
        """I can sort a PydanticSequence in place."""
        exp = sorted(users_data, key=lambda x: x["age"], reverse=True)
        assert users.model_dump() != exp
        result = users.sort(key=lambda x: x.age, reverse=True)
        assert result is None
        assert users.model_dump() == exp

    def test_assignment_validation(
        self, users: UsersSequence, users_data: UsersData
    ) -> None:  # sourcery skip: class-extract-method
        """When I add elements ot the PydanticSequence, they are validated."""
        assert users.model_dump() == users_data
        checked_once = False
        for user_data in users_data:
            users.append(User(**user_data))
            checked_once = True
        assert checked_once
        assert users.model_dump() == users_data + users_data
        with pytest.raises(pdt.ValidationError):
            # Appending an element of the wrong type raises an error.
            users.append(users_data[0])  # type: ignore

    def test_weak_assignment_validation(
        self,
        weak_users_sequence: WeakUsersSequence,
        user_count: int,
        users_data: UsersData,
    ) -> None:
        """When I add elements ot the PydanticSequence, they are validated."""
        assert weak_users_sequence.model_dump() == users_data
        checked_once = False
        for user_data in users_data:
            weak_users_sequence.append(User(**user_data))
            checked_once = True
        assert checked_once
        checked_once = False
        assert weak_users_sequence.model_dump() == users_data + users_data
        for user_data in users_data:
            # Appending a dictionary version of the element model is allowed.
            weak_users_sequence.append(user_data)  # type: ignore
            checked_once = True
        assert checked_once
        checked_once = False
        for i, user_data in enumerate(users_data):
            assert weak_users_sequence[i + user_count] == User(**user_data)
            checked_once = True
        assert checked_once
        with pytest.raises(pdt.ValidationError):
            # Appending an element of the wrong type raises an error.
            weak_users_sequence.append("user")  # type: ignore


@pytest.mark.parametrize(
    "users, json_str",
    [
        pytest.param(
            HasUsersSequence(
                users=UsersSequence(
                    User(name="Alice", age=30),
                    User(name="Bob", age=40),
                )
            ),
            '{"users":[{"name":"Alice","age":30},{"name":"Bob","age":40}]}',
            id="two users",
        ),
    ],
)
class TestUsageInPydanticModels:
    """I should be able to use PydanticSequence in Pydantic models."""

    def test_serialization(self, users: HasUsersSequence, json_str: str) -> None:
        """I can serialize PydanticSequence objects to JSON."""
        assert users.model_dump_json() == json_str

    def test_deserialization(self, json_str: str, users: HasUsersSequence) -> None:
        """I can deserialize JSON to PydanticSequence objects."""
        assert HasUsersSequence.model_validate_json(json_str) == users
