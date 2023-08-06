"""Tests for `pydantic_collections.mapping` module."""
import json
import typing as t

import pydantic as pdt
import pytest

from pydantic_collections.core import CollectionModelConfig
from pydantic_collections.mapping import PydanticMapping


class User(pdt.BaseModel):
    """A user."""

    name: str
    age: int


class UsersMapping(PydanticMapping[User]):
    """A mapping of users."""


class WeakUsersMapping(PydanticMapping[User]):
    """A mapping of users with weak validation."""

    model_config = CollectionModelConfig(validate_assignment_strict=False)


class UserData(t.TypedDict):
    """Dict version of User."""

    name: str
    age: int


UsersData = dict[str, UserData]
UsersMappingData = dict[str, User]


class HasUsersMapping(pdt.BaseModel):
    """A class with a PydanticMapping."""

    users: UsersMapping


@pytest.fixture()
def user_count() -> int:
    """Return number of users."""
    return 2


@pytest.fixture()
def users_data(user_count: int) -> UsersData:
    """Return data for multiple users."""
    return {
        f"User {i}": dict(name=f"Name {i}", age=i)  # type: ignore
        for i in range(user_count)
    }


@pytest.fixture()
def users_mapping_data(users_data: UsersData) -> UsersMappingData:
    """Return data for multiple users."""
    return {k: User(**v) for k, v in users_data.items()}


@pytest.fixture()
def users(users_mapping_data: UsersMappingData) -> UsersMapping:
    """Return multiple users."""
    return UsersMapping(users_mapping_data)


@pytest.fixture()
def weak_users_mapping(users_data: UsersMappingData) -> WeakUsersMapping:
    """Return multiple users."""
    return WeakUsersMapping(users_data)


class TestPydanticMapping:
    """Tests for `PydanticMapping`."""

    def test_length(self, users: UsersMapping, user_count: int) -> None:
        """I can get the length of a PydanticMapping."""
        assert len(users) == user_count

    def test_get_item(self, users: UsersMapping, users_data: UsersData) -> None:
        """I can get an item from a PydanticMapping by indexing it."""
        checked_once = False
        for i, user_data in enumerate(users_data.values()):
            assert users[f"User {i}"] == User(**user_data)
            checked_once = True
        assert checked_once

    def test_get_item_invalid_key(self, users: UsersMapping) -> None:
        """I get a KeyError when I try to get an item with an invalid key."""
        with pytest.raises(KeyError):
            users["Invalid key"]

    def test_assignment_validation(
        self, users: UsersMapping, users_data: UsersData
    ) -> None:
        """I can set an item in a PydanticMapping by indexing it."""
        checked_once = False
        for i, user_data in enumerate(users_data.values()):
            assert users[f"User {i}"] == User(**user_data)
            new_user = User(name=f"New name {i}", age=i + 1)
            users[f"User {i}"] = new_user
            assert users[f"User {i}"] == new_user
            checked_once = True
        assert checked_once
        newer_user = User(name="Newer name", age=3)
        assert "Newer key" not in users
        users["Newer key"] = newer_user
        assert users["Newer key"] == newer_user
        with pytest.raises(pdt.ValidationError):
            # Setting an item of the wrong type raises an error.
            users["Invalid key"] = users_data["User 0"]  # type: ignore

    def test_model_dump(self, users: UsersMapping, users_data: UsersData) -> None:
        """I can dump a PydanticMapping to a dict."""
        assert users.model_dump() == users_data

    def test_model_dump_json(self, users: UsersMapping, users_data: UsersData) -> None:
        """I can dump a PydanticMapping to a JSON string."""
        model_dump_json = users.model_dump_json()
        json_dumps = json.dumps(users_data)
        assert json.loads(model_dump_json) == json.loads(json_dumps)

    def test_model_validate(self, users: UsersMapping, users_data: UsersData) -> None:
        """I can validate a PydanticSequence."""
        assert UsersMapping.model_validate(users_data) == users

    def test_model_validate_json(
        self, users: UsersMapping, users_data: UsersData
    ) -> None:
        """I can validate a PydanticSequence from JSON."""
        assert UsersMapping.model_validate_json(json.dumps(users_data)) == users

    def test_weak_assignment_validation(
        self,
        weak_users_mapping: WeakUsersMapping,
        user_count: int,
        users_data: UsersData,
    ) -> None:
        """When I add elements ot the PydanticSequence, they are validated."""
        assert weak_users_mapping.model_dump() == users_data
        checked_once = False
        for user_data in users_data.values():
            weak_users_mapping[f"User {len(weak_users_mapping)}"] = User(**user_data)
            checked_once = True
        assert checked_once
        checked_once = False
        for user_data in users_data.values():
            # Appending a dictionary version of the element model is allowed.
            weak_users_mapping[
                f"User {len(weak_users_mapping)}"
            ] = user_data  # type: ignore
            checked_once = True
        assert checked_once
        checked_once = False
        for i, user_data in enumerate(users_data.values()):
            assert weak_users_mapping[f"User {i + user_count}"] == User(**user_data)
            checked_once = True
        assert checked_once
        with pytest.raises(pdt.ValidationError):
            # Appending an element of the wrong type raises an error.
            weak_users_mapping.append("user")  # type: ignore
