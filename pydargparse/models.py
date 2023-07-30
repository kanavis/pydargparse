import enum
from typing import Optional, Any, Callable, Type, TypeVar


class Undefined:
    pass


TAppArguments = TypeVar("TAppArguments", bound="AppArguments")


class AppArguments:
    _pydargparse_args: dict[str, Any]
    _pydargparse_sub_args: dict[Type[TAppArguments], TAppArguments]

    def pydargparse_get_sub_args(self, sub_args_type: Type[TAppArguments]) -> TAppArguments:
        try:
            return self._pydargparse_sub_args[sub_args_type]
        except KeyError:
            raise ValueError("Sub arguments type {} wasn't registered in {}".format(sub_args_type, self.__class__))


class ListStyle(enum.Enum):
    REPEAT_KEY = "repeat_key"
    REPEAT_VALUE = "repeat_value"


class Argument:
    def __init__(
        self,
        alias: Optional[str] = None,
        *,
        default: Any = Undefined,
        default_factory: Optional[Callable[[], Any]] = None,
        custom_type: Optional[Callable[[str], Any]] = None,
        post_validator: Optional[Callable[[Any], Any]] = None,
        required: Optional[bool] = None,
        help_: Optional[str] = None,
        metavar: Optional[str] = None,
        list_style: ListStyle = ListStyle.REPEAT_KEY,
        custom_type_requires_list: bool = False,
    ):
        self.alias = alias
        self.default = default
        self.default_factory = default_factory
        if self.default is not Undefined and self.default_factory is not None:
            raise ValueError("Cannot use both 'default' and 'default_factory' for the same field")
        self.custom_type = custom_type
        self.post_validator = post_validator
        if required is False and (default is not Undefined or default_factory is not None):
            raise ValueError("Cannot use 'required=False' when default value exists")
        self.required = required
        self.help = help_
        self.metavar = metavar
        self.list_style = list_style
        if custom_type_requires_list and custom_type is None:
            raise ValueError("Cannot use 'custom_type_requires_list' without 'custom_type'")
        self.custom_type_requires_list = custom_type_requires_list

    def __set_name__(self, owner, name):
        self._name = name

    def __get__(self, instance, owner):
        return getattr(instance, "_pydargparse_args")[self._name]

    def __set__(self, instance, value):
        raise TypeError("Argument attributes are immutable")


class SubCommandArguments(AppArguments):
    __command__: str
