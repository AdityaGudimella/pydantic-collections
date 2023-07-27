"""A collection of Pydantic models for common data structures."""
__title__ = "pydantic-collections"
__version__ = "0.5.2"

from pathlib import Path

from .core import CollectionModelConfig
from .sequence import PydanticSequence

REPO_ROOT = Path(__file__).parent.parent.resolve()


__all__ = ["__title__", "__version__", "CollectionModelConfig", "PydanticSequence"]
