# pydantic-collections

[![Build Status](https://app.travis-ci.com/romis2012/pydantic-collections.svg?branch=master)](https://app.travis-ci.com/romis2012/pydantic-collections)
[![Coverage Status](https://coveralls.io/repos/github/romis2012/pydantic-collections/badge.svg?branch=master&_=x)](https://coveralls.io/github/romis2012/pydantic-collections?branch=master)
[![PyPI version](https://badge.fury.io/py/pydantic-collections.svg)](https://badge.fury.io/py/pydantic-collections)

The `pydantic-collections` package provides `PydanticSequence` class that allows you
to manipulate collections of [pydantic](https://github.com/samuelcolvin/pydantic) models
(and any other types supported by pydantic).

## Requirements

- Python>=3.7
- pydantic>=1.8.2,<3.0

## Installation

```bash
pip install pydantic-collections
```

## Usage

### Basic usage

```python

from datetime import datetime

from pydantic import BaseModel
from pydantic_collections import PydanticSequence


class User(BaseModel):
    id: int
    name: str
    birth_date: datetime


class UserCollection(PydanticSequence[User]):
    pass


 user_data = [
        {'id': 1, 'name': 'Bender', 'birth_date': '2010-04-01T12:59:59'},
        {'id': 2, 'name': 'Balaganov', 'birth_date': '2020-04-01T12:59:59'},
    ]

users = UserCollection(user_data)

print(users)
#> UserCollection([User(id=1, name='Bender', birth_date=datetime.datetime(2010, 4, 1, 12, 59, 59)), User(id=2, name='Balaganov', birth_date=datetime.datetime(2020, 4, 1, 12, 59, 59))])

print(users.model_dump())  # pydantic v2.x
#> [{'id': 1, 'name': 'Bender', 'birth_date': datetime.datetime(2010, 4, 1, 12, 59, 59)}, {'id': 2, 'name': 'Balaganov', 'birth_date': datetime.datetime(2020, 4, 1, 12, 59, 59)}]

print(users.model_dump_json()) # pydantic v2.x
#> [{"id": 1, "name": "Bender", "birth_date": "2010-04-01T12:59:59"}, {"id": 2, "name": "Balaganov", "birth_date": "2020-04-01T12:59:59"}]
```

### Strict assignment validation

By default `PydanticSequence` has a strict assignment check

```python
...
users = UserCollection()
users.append(User(id=1, name='Bender', birth_date=datetime.utcnow()))  # OK
users.append({'id': 1, 'name': 'Bender', 'birth_date': '2010-04-01T12:59:59'})
#>  instance of User expected (type=type_error.arbitrary_type; expected_arbitrary_type=User)
```

This behavior can be changed via Model Config

Pydantic v2.x

```python
from pydantic_collections import PydanticSequence, CollectionModelConfig
...
class UserCollection(PydanticSequence[User]):
    model_config = CollectionModelConfig(validate_assignment_strict=False)
```

```python
users = UserCollection()
users.append({'id': 1, 'name': 'Bender', 'birth_date': '2010-04-01T12:59:59'})  # OK
assert users[0].__class__ is User
assert users[0].id == 1
```

### Using as a model field

`PydanticSequence` is a subclass of `pydantic.RootModel`, so you can use it as a model
field

```python
...
class UserContainer(BaseModel):
    users: UserCollection = []

data = {
    'users': [
        {'id': 1, 'name': 'Bender', 'birth_date': '2010-04-01T12:59:59'},
        {'id': 2, 'name': 'Balaganov', 'birth_date': '2020-04-01T12:59:59'},
    ]
}

container = UserContainer(**data)
container.users.append(User(...))
...
```
