import contextlib
import io
import unittest
from typing import Type, Optional, Pattern, AnyStr, List, Set, Union, TypeVar

from pydargparse.models import AppArguments, SubCommandArguments, Argument, ListStyle
from pydargparse.parse import parse_args
from pydargparse.decorators import post_validator, register_sub_args

TAppArguments = TypeVar("TAppArguments", bound=AppArguments)


class _BaseParseTestCase(unittest.TestCase):
    def _check_dict(self, base_path: str, data, reference: dict):
        if not isinstance(data, (AppArguments, SubCommandArguments)):
            raise AssertionError("'{}': AppArguments|SubCommandArguments expected, got {!r}".format(base_path, data))
        for ref_k, ref_v in reference:
            if ref_k not in data._pydargparse_args:
                raise AssertionError("'{}{}': missing field in parse result".format(base_path, ref_k))
            if ref_k == "__command__":
                self.assertIsInstance(data, SubCommandArguments, "'{}': not a SubCommandArguments".format(base_path))
                self.assertEqual(data.__command__, ref_v, "'{}': __command__ is not '{}'".format(base_path, ref_v))
            else:
                real_v = data._pydargparse_args[ref_k]
                if callable(ref_v):
                    ref_v(real_v)
                else:
                    if isinstance(ref_v, dict):
                        self._check_dict("{}{}.".format(base_path, ref_k), real_v, ref_v)
                    self.assertEqual(real_v, ref_v, "'{}{}': {!r} expected, got {!r}".format(base_path, ref_k, ref_v, real_v))

    def _check(
        self, arg_type: Type[TAppArguments], args: list[str], reference: dict, enable_sub_args: Optional[list[str]] = None,
    ) -> TAppArguments:
        result = parse_args(arg_type=arg_type, args=args, enable_sub_args=enable_sub_args)
        self._check_dict("", result, reference)
        return result

    def _check_error(
        self, arguments: Type[AppArguments], args: list[str], expected_error: Optional[Union[str, Pattern[AnyStr]]] = None,
    ):
        f = io.StringIO()
        with contextlib.redirect_stderr(f):
            with self.assertRaises(SystemExit):
                parse_args(arguments, args)

        if expected_error is not None:
            self.assertRegex(f.getvalue(), expected_error)


class TestParseBaseTypes(_BaseParseTestCase):
    def test_int(self):
        class Args(AppArguments):
            test_arg: int

        self._check(Args, ["--test-arg", "10"], {"test_arg": 10})

    def test_str(self):
        class Args(AppArguments):
            test_arg: str

        self._check(Args, ["--test-arg", "some string"], {"test_arg": "some string"})

    def test_float(self):
        class Args(AppArguments):
            test_arg: float

        self._check(Args, ["--test-arg", "1.2"], {"test_arg": 1.2})

    def test_bool(self):
        class Args(AppArguments):
            test_arg: bool

        self._check(Args, ["--test-arg"], {"test_arg": True})

    def test_bool_not_passed(self):
        class Args(AppArguments):
            test_arg: bool

        self._check(Args, [], {"test_arg": False})

    def test_type_validation__fails(self):
        class Args(AppArguments):
            test_arg: int

        self._check_error(Args, [], r"the following arguments are required: --test-arg")

    def test_optional(self):
        class Args(AppArguments):
            test_arg: Optional[int]

        self._check(Args, [], {"test_arg": None})

    def test_multiple_fields(self):
        class Args(AppArguments):
            test_arg: int
            test_arg1: str
            test_arg2: float

        self._check(
            Args,
            ["--test-arg", "10", "--test-arg1", "some string", "--test-arg2", "1.2"],
            {"test_arg": 10, "test_arg1": "some string", "test_arg2": 1.2},
        )


class TestCommonList(_BaseParseTestCase):
    def test_pep585_int(self):
        class Args(AppArguments):
            test_arg: list[int]

        self._check(Args, ["--test-arg", "10", "--test-arg", "20"], {"test_arg": [10, 20]})

    def test_pep585_str(self):
        class Args(AppArguments):
            test_arg: list[str]

        self._check(
            Args,
            ["--test-arg", "some string", "--test-arg", "other string"],
            {"test_arg": ["some string", "other string"]},
        )

    def test_pep585_float(self):
        class Args(AppArguments):
            test_arg: list[float]

        self._check(Args, ["--test-arg", "1.2", "--test-arg", "2.3"], {"test_arg": [1.2, 2.3]})

    def test_legacy_int(self):
        class Args(AppArguments):
            test_arg: List[int]

        self._check(Args, ["--test-arg", "10", "--test-arg", "20"], {"test_arg": [10, 20]})

    def test_legacy_str(self):
        class Args(AppArguments):
            test_arg: List[str]

        self._check(
            Args,
            ["--test-arg", "some string", "--test-arg", "other string"],
            {"test_arg": ["some string", "other string"]},
        )

    def test_legacy_float(self):
        class Args(AppArguments):
            test_arg: List[float]

        self._check(Args, ["--test-arg", "1.2", "--test-arg", "2.3"], {"test_arg": [1.2, 2.3]})

    def test_empty(self):
        class Args(AppArguments):
            test_arg: list[str]

        self._check(Args, [], {"test_arg": []})

    def test_empty_required__fails(self):
        class Args(AppArguments):
            test_arg: list[str] = Argument(required=True)

        self._check_error(Args, [], r"the following arguments are required: --test-arg")


class TestCommonSet(_BaseParseTestCase):
    def test_pep585_int(self):
        class Args(AppArguments):
            test_arg: set[int]

        self._check(Args, ["--test-arg", "10", "--test-arg", "20"], {"test_arg": {10, 20}})

    def test_pep585_str(self):
        class Args(AppArguments):
            test_arg: set[str]

        self._check(
            Args,
            ["--test-arg", "some string", "--test-arg", "other string"],
            {"test_arg": {"some string", "other string"}},
        )

    def test_pep585_float(self):
        class Args(AppArguments):
            test_arg: set[float]

        self._check(Args, ["--test-arg", "1.2", "--test-arg", "2.3"], {"test_arg": {1.2, 2.3}})

    def test_legacy_int(self):
        class Args(AppArguments):
            test_arg: Set[int]

        self._check(Args, ["--test-arg", "10", "--test-arg", "20"], {"test_arg": {10, 20}})

    def test_legacy_str(self):
        class Args(AppArguments):
            test_arg: Set[str]

        self._check(
            Args,
            ["--test-arg", "some string", "--test-arg", "other string"],
            {"test_arg": {"some string", "other string"}},
        )

    def test_legacy_float(self):
        class Args(AppArguments):
            test_arg: Set[float]

        self._check(Args, ["--test-arg", "1.2", "--test-arg", "2.3"], {"test_arg": {1.2, 2.3}})

    def test_empty(self):
        class Args(AppArguments):
            test_arg: set[str]

        self._check(Args, [], {"test_arg": {}})

    def test_empty_required__fails(self):
        class Args(AppArguments):
            test_arg: set[str] = Argument(required=True)

        self._check_error(Args, [], r"the following arguments are required: --test-arg")


class TestRepeatValueStyleList(_BaseParseTestCase):
    def test_str(self):
        class Args(AppArguments):
            test_arg: list[str] = Argument(list_style=ListStyle.REPEAT_VALUE)

        self._check(Args, ["--test-arg", "some string", "other string"], {"test_arg": ["some string", "other string"]})


class TestCustomType(_BaseParseTestCase):
    class CustomType:
        def __init__(self, value: str):
            self.value = value

        def __eq__(self, other):
            return other.value == self.value

    def test_simple(self):
        class Args(AppArguments):
            test_arg: TestCustomType.CustomType

        self._check(Args, ["--test-arg", "some string"], {"test_arg": TestCustomType.CustomType("some string")})

    def test_common_list(self):
        class Args(AppArguments):
            test_arg: list[TestCustomType.CustomType] = Argument(custom_type_requires_list=True)

        self._check(
            Args,
            ["--test-arg", "some string", "--test-arg", "other string"],
            {"test_arg": [TestCustomType.CustomType("some string"), TestCustomType.CustomType("other string")]},
        )

    def test_repeat_value_style_list(self):
        class Args(AppArguments):
            test_arg: list[TestCustomType.CustomType] = Argument(
                custom_type_requires_list=True, list_style=ListStyle.REPEAT_VALUE,
            )

        self._check(
            Args,
            ["--test-arg", "some string", "other string"],
            {"test_arg": [TestCustomType.CustomType("some string"), TestCustomType.CustomType("other string")]},
        )

    def test_empty_list(self):
        class Args(AppArguments):
            test_arg: list[TestCustomType.CustomType] = Argument(custom_type_requires_list=True)

        self._check(Args, [], {"test_arg": []})

    def test_empty_list_required__fail(self):
        class Args(AppArguments):
            test_arg: list[TestCustomType.CustomType] = Argument(custom_type_requires_list=True, required=True)

        self._check_error(Args, [], r"the following arguments are required: --test-arg")


class TestSubCommand(_BaseParseTestCase):
    def _make_base_subcommand(self, optional=True):
        class SubCommand1(SubCommandArguments):
            __command__ = "command1"
            subcommand1_arg: int

        class SubCommand2(SubCommandArguments):
            __command__ = "command2"
            subcommand2_arg: int

        if optional:
            class Args(AppArguments):
                command_arg: int
                subcommand: Optional[Union[SubCommand1, SubCommand2]]
        else:
            class Args(AppArguments):
                command_arg: int
                subcommand: Union[SubCommand1, SubCommand2]

        return Args

    def test_base_cmd1(self):
        self._check(
            self._make_base_subcommand(),
            ["--command-arg", "some string", "command1", "--subcommand1-arg", 1],
            {"command_arg": "some string", "subcommand": {"__command__": "command1", "subcommand1_arg": 1}},
        )

    def test_base_cmd2(self):
        self._check(
            self._make_base_subcommand(),
            ["--command-arg", "some string", "command2", "--subcommand2-arg", 1],
            {"command_arg": "some string", "subcommand": {"__command__": "command2", "subcommand2_arg": 1}},
        )

    def test_cmd1_with_cmd2_args__fail(self):
        self._check_error(
            self._make_base_subcommand(),
            ["--command-arg", "some string", "command1", "--subcommand2-arg", 1],
            r"unrecognized arguments: --subcommand2-arg",
        )

    def test_cmd1_with_pre_cmd_args__fail(self):
        self._check_error(
            self._make_base_subcommand(),
            ["--command-arg", "some string", "--subcommand1-arg", 1, "command1"],
            r"unrecognized arguments: --subcommand1-arg",
        )

    def test_cmd1_with_post_cmd_base_args__fail(self):
        self._check_error(
            self._make_base_subcommand(),
            ["command1", "--subcommand1-arg", 1, "--command-arg", "some string"],
            r"unrecognized arguments: --command-arg",
        )

    def test_optional(self):
        self._check(
            self._make_base_subcommand(optional=True),
            ["--command-arg", "some string"],
            {"command_arg": "some string", "subcommand": None},
        )

    def test_required__fail(self):
        self._check_error(
            self._make_base_subcommand(),
            ["command1", "--subcommand1-arg", 1, "--command-arg", "some string"],
            r"the following arguments are required: subcommand",
        )


class TestParsing(_BaseParseTestCase):
    def test_base_validator__fail(self):
        class Args(AppArguments):
            test_arg: int
            
        self._check_error(Args, ["--test-arg", "a"], r"argument --test-arg: invalid int value: 'a'")

    def test_custom_pre_validator__fail(self):
        def custom_fail_validator(val: str):
            raise ValueError("Value {!r} is wrong".format(val))

        class Args(AppArguments):
            test_arg: int = Argument(custom_type=custom_fail_validator)

        self._check_error(Args, ["--test-arg", "a"], r"argument --test-arg: Value 'a' is wrong")

    def test_custom_functional_post_validator__fail(self):
        def custom_fail_validator(val: float):
            raise ValueError("Value {!r} is wrong".format(val))

        class Args(AppArguments):
            test_arg: float = Argument(post_validator=custom_fail_validator)

        self._check_error(Args, ["--test-arg", "1.0"], r"argument --test-arg: Value 1.0 is wrong")

    def test_custom_functional_post_validator__change_val(self):
        def custom_change_validator(val: int):
            return 1 + val

        class Args(AppArguments):
            test_arg: int = Argument(post_validator=custom_change_validator)

        self._check(Args, ["--test-arg", "1"], {"test_arg": "2"})

    def test_custom_decorator_post_validator__fail(self):
        class Args(AppArguments):
            test_arg: float

            @post_validator("test_arg")
            def validate(self, val: float):
                raise ValueError("Value {!r} is wrong".format(val))

        self._check_error(Args, ["--test-arg", "1.0"], r"argument --test-arg: Value 1.0 is wrong")

    def test_custom_decorator_post_validator__change_val(self):
        class Args(AppArguments):
            test_arg: int

            @post_validator("test_arg")
            def validate(self, val: int):
                return 1 + val

        self._check(Args, ["--test-arg", "1"], {"test_arg": "2"})

    def test_alias(self):
        class Args(AppArguments):
            test_arg: str = Argument(alias="alias_arg")

        self._check(Args, ["--alias-arg", "some string"], {"alias_arg": "some string"})

    def test_alias_fail_base(self):
        class Args(AppArguments):
            test_arg: Optional[str] = Argument(alias="alias_arg")

        self._check_error(Args, ["--alias-arg", "some string"], "unrecognized arguments: --test-arg")

    def test_default_val__ok(self):
        class Args(AppArguments):
            test_arg: str = Argument(default="some string")

        self._check(Args, [], {"test_arg": "some string"})

    def test_default_val__overriden(self):
        class Args(AppArguments):
            test_arg: str = Argument(default="some string")

        self._check(Args, ["--test-arg", "other string"], {"test_arg": "other string"})

    def test_default_factory__ok(self):
        class Args(AppArguments):
            test_arg: list[str] = Argument(default_factory=list)

        self._check(Args, [], {"test_arg": []})

    def test_default_factory__overriden(self):
        class Args(AppArguments):
            test_arg: list[str] = Argument(default_factory=list)

        self._check(Args, ["--test-arg", "other string"], {"test_arg": ["other string"]})

    def test_help(self):
        class Args(AppArguments):
            test_arg: str = Argument(help_="test help message")

        self._check_error(Args, ["--help"], r"test help message")

    def test_metavar(self):
        class Args(AppArguments):
            test_arg: str = Argument(metavar="TEST_METAVAR")

        self._check_error(Args, ["--help"], r"TEST_METAVAR")


class TestArgumentSubsets(_BaseParseTestCase):
    def test_declarative_style(self):
        class SubArgs(AppArguments):
            test_sub_arg: str

        class Args(AppArguments):
            test_arg: str
            sub_args: SubArgs

        self._check(
            Args,
            ["--test-arg", "some string", "--test-sub-arg", "some other string"],
            {"test_arg": "some string", "sub_args": {"test_sub_arg": "some other string"}},
        )

    def test_declarative_style__optional_enable(self):
        class SubArgs(AppArguments):
            test_sub_arg: str

        class Args(AppArguments):
            test_arg: str
            sub_args: Optional[SubArgs]

        self._check(
            Args,
            ["--test-arg", "some string", "--test-sub-arg", "some other string"],
            {"test_arg": "some string", "sub_args": {"test_sub_arg": "some other string"}},
            enable_sub_args=["sub_args"],
        )

    def test_declarative_style__optional_disable(self):
        class SubArgs(AppArguments):
            test_sub_arg: str

        class Args(AppArguments):
            test_arg: str
            sub_args: Optional[SubArgs]

        self._check(Args, ["--test-arg", "some string"], {"test_arg": "some string", "sub_args": None})

    def test_imperative_style__simple(self):
        class SubArgs(AppArguments):
            test_sub_arg: str

        class Args(AppArguments):
            test_arg: str

        register_sub_args(Args, SubArgs)

        result = self._check(
            Args,
            ["--test-arg", "some string", "--test-sub-arg", "some other string"],
            {"test_arg": "some string"},
        )
        self._check_dict("sub_args:", result.pydargparse_get_sub_args(SubArgs), {"test_sub_arg": "some other string"})

    def test_imperative_style__prefix(self):
        class SubArgs(AppArguments):
            test_sub_arg: str

        class Args(AppArguments):
            test_arg: str

        register_sub_args(Args, SubArgs, prefix="prefix1")

        result = self._check(
            Args,
            ["--test-arg", "some string", "--prefix1-test-sub-arg", "some other string"],
            {"test_arg": "some string"},
        )
        self._check_dict("sub_args:", result.pydargparse_get_sub_args(SubArgs), {"test_sub_arg": "some other string"})

    def test_imperative_style__non_registered__fail(self):
        class SubArgs(AppArguments):
            test_sub_arg: str

        class Args(AppArguments):
            test_arg: str

        result = self._check(
            Args,
            ["--test-arg", "some string", "--prefix1-test-sub-arg", "some other string"],
            {"test_arg": "some string"},
        )
        with self.assertRaisesRegex(ValueError, r"Sub arguments type.+SubArgs.+wasn't registered in.+Args.+"):
            result.pydargparse_get_sub_args(SubArgs)
