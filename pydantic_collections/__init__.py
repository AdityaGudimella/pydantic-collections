__title__ = 'pydantic-collections'
__version__ = '0.5.0'

from pydantic.version import VERSION as PYDANTIC_VERSION

PYDANTIC_V2 = PYDANTIC_VERSION.startswith('2.')


if PYDANTIC_V2:
    from ._v2 import BaseCollectionModel, CollectionModelConfig

    __all_v__ = ('CollectionModelConfig',)
else:
    from ._v1 import BaseCollectionModel

    __all_v__ = ()

__all__ = (
    '__title__',
    '__version__',
    'BaseCollectionModel',
) + __all_v__
