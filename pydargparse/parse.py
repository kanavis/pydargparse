import argparse
import inspect
from collections.abc import Collection, Sequence
from typing import Type, Optional, Any, TypeVar

from pydargparse.models import AppArguments

TAppArguments = TypeVar("TAppArguments", bound=AppArguments)


def _get_default_args(func):
    return {k: v.default for k, v in inspect.signature(func).parameters.items() if v.default is not inspect.Parameter.empty}


def _resolve_config(arguments: Type[TAppArguments], arg_name: str, default_values: dict[str, Any]):
    config = getattr(arguments, "Config", None)
    if config is None or not hasattr(config, arg_name):
        return default_values[arg_name]
    return getattr(config, arg_name)


def parse_args(
    arg_type: Type[TAppArguments],
    args: Optional[Sequence[str]] = None,
    enable_sub_args: Optional[Collection[str]] = None,
) -> Optional[TAppArguments]:
    default_args = _get_default_args(argparse.ArgumentParser.__init__)
    parser = argparse.ArgumentParser(
        prog=_resolve_config(arg_type, "prog", default_args),
        usage=_resolve_config(arg_type, "usage", default_args),
        description=_resolve_config(arg_type, "description", default_args),
        epilog=_resolve_config(arg_type, "epilog", default_args),
        formatter_class=_resolve_config(arg_type, "formatter_class", default_args),
        prefix_chars=_resolve_config(arg_type, "prefix_chars", default_args),
        fromfile_prefix_chars=_resolve_config(arg_type, "fromfile_prefix_chars", default_args),
        add_help=_resolve_config(arg_type, "add_help", default_args),
        allow_abbrev=_resolve_config(arg_type, "allow_abbrev", default_args),
        exit_on_error=_resolve_config(arg_type, "exit_on_error", default_args),
    )
    parser.add_argument()
    args = parser.parse_args(args=args)

    return arg_type()
