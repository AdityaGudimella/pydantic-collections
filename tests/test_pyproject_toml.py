"""Tests to ensure that pyproject.toml is valid and consistent."""
import typing as t
from itertools import chain

import pytest
import toml

from pydantic_collections import REPO_ROOT, __version__


@pytest.fixture()
def pyproject_config() -> t.Dict[str, t.Any]:
    """Load the pyproject.toml file."""
    pyproject_file_path = REPO_ROOT / "pyproject.toml"
    return toml.load(pyproject_file_path)


@pytest.fixture()
def all_dependencies(pyproject_config: t.Dict[str, t.Any]) -> t.Dict[str, t.Any]:
    """Return dependencies installed when running `pip install llegom[all]`."""
    return pyproject_config["tool"]["poetry"]["dependencies"]


@pytest.fixture()
def all_extra_dependencies(pyproject_config: t.Dict[str, t.Any]) -> t.List[str]:
    """Return dependencies that are not installed when running `pip install llegom`."""
    extras = pyproject_config["tool"]["poetry"]["extras"]
    return list(chain.from_iterable(extras.values()))


def test_pyproject_optional_present_in_option(
    all_dependencies: t.Dict[str, t.Any], all_extra_dependencies: t.List[str]
) -> None:
    """Ensure that the optional dependencies are present in the at least one of the
    options section.

    If this test fails, it means that there is some dependency with optional = true, but
    will never get installed because no option in tool.poetry.extras requires it.
    """
    for dependency, options in all_dependencies.items():
        if isinstance(options, dict) and "optional" in options and options["optional"]:
            assert dependency in all_extra_dependencies


def test_pyproject_install_all(
    pyproject_config: t.Dict[str, t.Any], all_dependencies: t.Dict[str, t.Any]
) -> None:
    """Installing using `pip install 'llegom[all]'` should install all dependencies."""  # noqa: E501
    extras = pyproject_config["tool"]["poetry"]["extras"]
    all_extras: t.Dict[str, str] = {k: v for k, v in extras.items() if k != "all"}
    all_extra_dependencies = chain.from_iterable(all_extras.values())
    extras_all = extras["all"]
    assert set(all_extra_dependencies) == set(extras_all)
    # If you specify a dependency in the extras section, make sure you mention it in
    # the actual dependencies section with the version number.
    for extra in all_extras.values():
        for dependency in extra:
            assert dependency in all_dependencies


def test_llegom_version(pyproject_config: t.Dict[str, t.Any]) -> None:
    """Ensure that the version of llegom in llegom/__init__.py is the same as in
    pyproject.toml.
    """
    poetry = pyproject_config["tool"]["poetry"]
    llegom_version = poetry["version"]
    assert llegom_version == __version__
