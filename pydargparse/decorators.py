from typing import Callable, Union, TypeVar, Generic, Optional, Type

from pydargparse.models import AppArguments

T = TypeVar("T")


class _PostValidator(Generic[T]):
    def __init__(self, fields: Union[str, list[str]], val_f: Callable[[T], T]):
        self.fields = fields
        self._val_f = val_f

    def validate(self, value: T) -> T:
        return self._val_f(value)


def post_validator(fields: Union[str, list[str]]) -> Callable[[Callable[[T], T]], _PostValidator[T]]:
    def decorator(external: Callable[[T], T]) -> _PostValidator[T]:
        return _PostValidator[T](fields, external)

    return decorator


class _SubArgsDefinition:
    def __init__(self, sub_args: Type[AppArguments], prefix: Optional[str]):
        self.sub_args = sub_args
        self.prefix = prefix


def register_sub_args(args: Type[AppArguments], sub_args: Type[AppArguments], prefix: Optional[str] = None):
    getattr(args, "_pydargparse_sub_args").append(_SubArgsDefinition(sub_args=sub_args, prefix=prefix))
