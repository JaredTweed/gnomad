# argumentor - A simple, copylefted, lightweight library to work with command-line arguments in Python
# Licensed under LGPLv3
# Copyright (C) 2021-2022 Twann <tw4nn@disroot.org>

import sys
import re
from .exceptions import (
    ExecNameError,
    OperationExistsError,
    OptionExistsError,
    ArgumentValueError,
    GroupExistsError,
    GroupNotExistsError,
    InvalidOptionError,
    InvalidOperationError,
)

__version__ = "1.1.0"


class Arguments:
    def __init__(
        self,
        arguments: list = None,
        exec_name: str = None,
        help_page: str = None,
        one_operation_required: bool = True,
        allow_short_args_together: bool = True,
        show_operation_groups_on_help_page: bool = True,
        show_option_groups_on_help_page: bool = True,
        copyright_header: str = None,
        more_info_footer: str = None,
    ) -> None:
        """
        Argumentor parser object
        :param arguments: Optional. Arguments to parse. If not set, sys.argv[1:] will be used
        :param exec_name: Optional. The name of the executable running. If not set, sys.argv[0] will be used
        :param help_page: Optional. Specify a custom help page as self.help_page. If None, argumentor will generate one
        :param one_operation_required: Defaults to True. If no operation is specified, the script will return an error
        :param allow_short_args_together: Defaults to True. Allow short arguments to be combined
        :param show_operation_groups_on_help_page: Defaults to True. Group operations by group on generated help page
        :param show_option_groups_on_help_page: Defaults to True. Group options by group on generated help page
        (ex. '-vz' instead of '-v -z')
        :param copyright_header: Optional. Specify a copyright header to be shown on generated help page
        :param more_info_footer: Optional. Add a custom message at the end of the generated help page
        """

        if arguments is None:
            self.arguments = sys.argv[1:]
        else:
            self.arguments = arguments

        if len(sys.argv) >= 1 and exec_name is None:
            self.exec_name = sys.argv[0]
        elif exec_name is None:
            raise ExecNameError("cannot find executable name")
        else:
            self.exec_name = exec_name

        self.one_operation_required = (
            one_operation_required  # One operation is required
        )
        self.allow_short_args_together = (
            allow_short_args_together  # Allow short args to be combined
        )

        self.operations = {}  # Available operations
        self.short_operations = {}  # Available short operations
        self.operation_groups = {}  # Existing operation groups
        self.options = {}  # Available options
        self.short_options = {}  # Available short options
        self.option_groups = {}  # Existing option groups

        self.active_operation = None  # The operation that is running
        self.isolate_unmatched = True  # Invalid args are stored as operation value

        self.output_operations = {}  # Operations result after parsing
        self.output_options = {}  # Options result after parsing

        self.show_operation_groups_on_help_page = show_operation_groups_on_help_page
        self.show_option_groups_on_help_page = show_option_groups_on_help_page
        self.copyright_header = copyright_header
        self.more_info_footer = more_info_footer

        if help_page:
            self.help_page = help_page
            self.generate_help_page = False
        else:
            self.help_page = self.__generate_help_page()
            self.generate_help_page = True

    def __generate_help_page(self) -> str:
        """
        :return: str: The help page
        """
        output = ""
        if self.copyright_header is not None:
            output += f"{self.copyright_header}\n"

        if self.operations is not None and self.options is None:
            output += f"usage: {self.exec_name} [operation] [arg(s)]\n\n"
        elif self.operations is None and self.options is not None:
            output += f"usage: {self.exec_name} [option(s)] [arg(s)]\n\n"
        elif self.operations is not None and self.options is not None:
            output += f"usage: {self.exec_name} [operation] [option(s)] [arg(s)]\n\n"
        else:
            output += f"usage: {self.exec_name} [arg(s)]\n\n"

        if self.operations != {}:
            output += "<operations>\n"

            for operation in self.operations:
                if self.operations[operation]["group"] is None:
                    line = ""
                    if not self.operations[operation]["hidden"]:
                        if self.operations[operation]["short_operation"] is not None:
                            line += f'  {self.operations[operation]["short_operation"]}'
                        line += f"  {operation}"
                        if self.operations[operation]["description"] is not None:
                            if len(line) > 15:
                                line += f'\t\t\t{self.operations[operation]["description"]}\n'
                            else:
                                line += f'\t\t\t\t{self.operations[operation]["description"]}\n'
                        else:
                            line += "\n"
                        output += line
            for group in self.operation_groups.keys():
                if self.show_operation_groups_on_help_page:
                    if self.operation_groups[group]["name"]:
                        output += f'* {self.operation_groups[group]["name"]}\n'
                    else:
                        output += f"* {group}\n"
                for operation in self.__get_operations_from_group(group):
                    line = ""
                    if not self.operations[operation]["hidden"]:
                        if self.operations[operation]["short_operation"] is not None:
                            line += f'  {self.operations[operation]["short_operation"]}'
                        line += f"  {operation}"
                        if self.operations[operation]["description"] is not None:
                            if len(line) > 15:
                                line += f'\t\t\t{self.operations[operation]["description"]}\n'
                            else:
                                line += f'\t\t\t\t{self.operations[operation]["description"]}\n'
                        else:
                            line += "\n"
                        output += line

        if self.options != {}:
            output += "\n<options>\n"

            for option in self.options:
                if self.options[option]["group"] is None:
                    line = ""
                    if not self.options[option]["hidden"]:
                        if self.options[option]["short_option"] is not None:
                            line += f'  {self.options[option]["short_option"]}'
                        line += f"  {option}"
                        if self.options[option]["description"] is not None:
                            if len(line) > 15:
                                line += f'\t\t\t{self.options[option]["description"]}\n'
                            else:
                                line += (
                                    f'\t\t\t\t{self.options[option]["description"]}\n'
                                )
                        else:
                            line += "\n"
                        output += line
            for group in self.option_groups.keys():
                if self.show_option_groups_on_help_page:
                    if self.option_groups[group]["name"]:
                        output += f'* {self.option_groups[group]["name"]}\n'
                    else:
                        output += f"* {group}\n"
                for option in self.__get_options_from_group(group):
                    line = ""
                    if not self.options[option]["hidden"]:
                        if self.options[option]["short_option"] is not None:
                            line += f'  {self.options[option]["short_option"]}'
                        line += f"  {option}"
                        if self.options[option]["description"] is not None:
                            if len(line) > 15:
                                line += f'\t\t\t{self.options[option]["description"]}\n'
                            else:
                                line += (
                                    f'\t\t\t\t{self.options[option]["description"]}\n'
                                )
                        else:
                            line += "\n"
                        output += line

        if self.more_info_footer is not None:
            output += f"\n{self.more_info_footer}"
        return output

    def __get_operations_from_group(self, group: str) -> list:
        if group not in self.operation_groups:
            raise GroupNotExistsError(f'operation group "{group}" does not exist')
        else:
            return self.operation_groups[group]["operations"]

    def __get_options_from_group(self, group: str) -> list:
        if group not in self.option_groups:
            raise GroupNotExistsError(f'option group "{group}" does not exist')
        else:
            return self.option_groups[group]["options"]

    def add_operation(
        self,
        operation: str,
        value_type,
        description: str = None,
        short_operation: str = None,
        required: bool = False,
        group: str = None,
        hidden: bool = False,
        default_value=None,
    ) -> None:
        """
        Add an operation to the list of supported arguments
        :param operation: The operation (ex. '--help')
        :param value_type: The type of the value to catch (bool, str, int, list).
        :param description: Optional. The description of what the operation does
        :param short_operation: Optional. The short version of the operation (ex. '-h')
        :param required: Defaults to False. Choose if the operation is required or not
        :param group: Optional. Specify an operation group
        :param hidden: Hide operation from help page
        :param default_value. Specify the default value to use if the argument is not passed. Defaults to None
        (or False for bool).

        :return:
        """
        if operation in self.operations.keys():
            raise OperationExistsError(f'operation "{operation}" already exists')
        elif operation in self.options.keys():
            raise OptionExistsError(f'option "{operation}" already exists')
        elif (
            short_operation is not None
            and short_operation in self.short_operations.keys()
        ):
            raise OperationExistsError(
                f'short operation "{short_operation}" already exists'
            )
        elif (
            short_operation is not None and short_operation in self.short_options.keys()
        ):
            raise OptionExistsError(f'short option "{short_operation}" already exists')
        elif value_type not in [bool, str, int, list]:
            raise ArgumentValueError(f'value type "{value_type}" is not supported')
        elif group is not None and group not in self.operation_groups:
            raise GroupNotExistsError(f'operation group "{group}" does not exist')
        elif (
            short_operation is not None
            and len(short_operation) > 1
            and not re.match(r"-[A-z\d]", short_operation)
        ):
            raise InvalidOperationError(
                f'short operation can only be one-character long when no dash, not "{short_operation}"'
            )
        elif short_operation is not None and len(short_operation) > 2:
            raise InvalidOperationError(
                f'short operation can contain a dash and a character maximum, not "{short_operation}"'
            )
        elif short_operation == operation:
            raise InvalidOperationError("short operation is equal to long operation")
        else:
            if default_value is None and value_type == bool:
                default_value = False
            elif default_value is not None and type(default_value) != value_type:
                raise ArgumentValueError(
                    f"default value for operation {operation} is from "
                    f'type "{type(default_value)}" instead of "{value_type}"'
                )
            self.operations[operation] = {
                "value_type": value_type,
                "description": description,
                "required": required,
                "group": group,
                "short_operation": short_operation,
                "default_value": default_value,
                "hidden": hidden,
            }
            if group is not None:
                self.operation_groups[group]["operations"].append(operation)
            if short_operation is not None:
                self.short_operations[short_operation] = operation
            if self.generate_help_page:
                self.help_page = self.__generate_help_page()

    def add_operation_group(self, group_name: str, name: str = None) -> None:
        """
        Create an operation group
        :param group_name: The name of the group
        :param name: Optional. Specify a different name to show on the help page.
        :return:
        """

        if group_name in self.operation_groups:
            raise GroupExistsError(f'operation group "{group_name}" already exists')
        else:
            self.operation_groups[group_name] = {"operations": [], "name": name}

    def add_option(
        self,
        option: str,
        value_type,
        description: str = None,
        short_option: str = None,
        required: bool = False,
        available_with_operations: list = None,
        required_by_operations: list = None,
        available_with_groups: list = None,
        required_by_groups: list = None,
        group: str = None,
        inherit_from_group: bool = True,
        hidden: bool = False,
        default_value=None,
    ) -> None:
        """
        Add an option to the list of supported arguments
        :param option: The option (ex. '--force')
        :param value_type: The type of the value to catch (bool, str, int, list).
        :param description: Optional. The description of what the operation does
        :param short_option: Optional. The short version of the operation (ex. '-f')
        :param required: Defaults to False. Choose if the operation is required or not
        :param available_with_operations: Optional. Option will only be available with operation in the list
        :param required_by_operations: Optional. Every operation in the list will fail without this option
        :param available_with_groups: Optional. Option will only be available with operation in the specified groups
        :param required_by_groups: Optional. Every operation in the specified groups will fail without this option
        :param group: Optional. Specify an option group
        :param inherit_from_group: Defaults to True. Inherit requirements and availability from group.
        :param hidden: Hide option from help page
        :param default_value. Specify the default value to use if the argument is not passed. Defaults to None
        (or False for bool).

        :return:
        """
        if option in self.options.keys():
            raise OptionExistsError(f'option "{option}" already exists')
        elif option in self.operations.keys():
            raise OperationExistsError(f'operation "{option}" already exists')
        elif short_option is not None and short_option in self.short_options.keys():
            raise OptionExistsError(f'short option "{option}" already exists')
        elif short_option is not None and short_option in self.short_operations.keys():
            raise OperationExistsError(
                f'short operation "{short_option}" already exists'
            )
        elif value_type not in [bool, str, int, list]:
            raise ArgumentValueError(f'value type "{value_type}" is not supported')
        elif group is not None and group not in self.option_groups.keys():
            raise GroupNotExistsError(f'option group "{group}" does not exist')
        elif not re.match(r"--[A-z\d\-]*", option):
            raise InvalidOptionError(
                f'option should start with two dashes: "--", not "{short_option}"'
            )
        elif short_option is not None and len(short_option) != 2:
            raise InvalidOptionError(
                f'short option must be two-characters long, not "{short_option}"'
            )
        elif short_option is not None and not re.match(r"-[A-z\d]", short_option):
            raise InvalidOptionError(
                f'short option must start with a dash and finish with a character, not "{short_option}"'
            )
        else:
            if default_value is None and value_type == bool:
                default_value = False
            elif default_value is not None and type(default_value) != value_type:
                raise ArgumentValueError(
                    f"default value for operation {option} is "
                    f'from type "{type(default_value)}" instead of "{value_type}"'
                )
            if group is not None and inherit_from_group:
                self.options[option] = {
                    "value_type": value_type,
                    "description": description,
                    "required": required,
                    "group": group,
                    "available_with_operations": self.option_groups[group][
                        "available_with_operations"
                    ],
                    "required_by_operations": self.option_groups[group][
                        "required_by_operations"
                    ],
                    "available_with_groups": self.option_groups[group][
                        "available_with_groups"
                    ],
                    "required_by_groups": self.option_groups[group][
                        "required_by_groups"
                    ],
                    "short_option": short_option,
                    "default_value": default_value,
                    "hidden": hidden,
                }
                if available_with_operations is not None:
                    self.options[option][
                        "available_with_operations"
                    ] = available_with_operations
                if required_by_operations is not None:
                    self.options[option][
                        "required_by_operations"
                    ] = required_by_operations
                if available_with_groups is not None:
                    self.options[option][
                        "available_with_groups"
                    ] = available_with_groups
                if required_by_groups is not None:
                    self.options[option]["required_by_groups"] = required_by_groups
            else:
                self.options[option] = {
                    "value_type": value_type,
                    "description": description,
                    "required": required,
                    "group": group,
                    "available_with_operations": available_with_operations,
                    "required_by_operations": required_by_operations,
                    "available_with_groups": available_with_groups,
                    "required_by_groups": required_by_groups,
                    "short_option": short_option,
                    "default_value": default_value,
                    "hidden": hidden,
                }
            if group is not None:
                self.option_groups[group]["options"].append(option)
            if short_option is not None:
                self.short_options[short_option] = option
            if self.generate_help_page:
                self.help_page = self.__generate_help_page()

    def add_option_group(
        self,
        group_name: str,
        name: str = None,
        available_with_operations: list = None,
        required_by_operations: list = None,
        available_with_groups: list = None,
        required_by_groups: list = None,
    ) -> None:
        """
        Create an option group
        :param group_name: The name of the groups
        :param name: Optional. Specify a different name to show on the help page.
        :param available_with_operations: Optional. Options will only be available with operation in the list
        :param required_by_operations: Optional. Every operation in the list will fail without these options
        :param available_with_groups: Optional. Options will only be available with operation in the specified groups
        :param required_by_groups: Optional. Every operation in the specified groups will fail without these options
        :return:
        """

        if group_name in self.option_groups.keys():
            raise GroupExistsError(f'option group "{group_name}" already exists')
        else:
            self.option_groups[group_name] = {
                "available_with_operations": available_with_operations,
                "required_by_operations": required_by_operations,
                "available_with_groups": available_with_groups,
                "required_by_groups": required_by_groups,
                "options": [],
                "name": name,
            }

    def __match_operation(
        self, operation_title: str, real_operation: str, real_argument: str
    ) -> None:
        if self.active_operation is None:
            self.active_operation = operation_title

            if len(real_argument.split("=")) == 2:
                if self.operations[operation_title]["value_type"] == int:
                    try:
                        self.output_operations[operation_title] = int(
                            real_argument.split("=")[1]
                        )
                        self.isolate_unmatched = False
                    except ValueError:
                        print(
                            f'Error: operation "{real_operation}" requires an integer'
                        )
                        raise SystemExit(1)
                elif self.operations[operation_title]["value_type"] == str:
                    if real_argument.split("=")[1]:
                        self.output_operations[operation_title] = str(
                            real_argument.split("=")[1]
                        )
                        self.isolate_unmatched = False
                    else:
                        print(
                            f'Error: operation "{real_operation}" requires at least one argument'
                        )
                        raise SystemExit(1)
                else:
                    print(
                        f'Error: operation "{real_operation}" does not support the "=" operator'
                    )
                    raise SystemExit(1)
            elif self.operations[operation_title]["value_type"] == bool:
                self.output_operations[operation_title] = True
            elif len(self.arguments) - self.arguments.index(real_argument) > 1:
                if self.operations[operation_title]["value_type"] == int:
                    self.output_operations[operation_title] = None
                    self.isolate_unmatched = True
                elif self.operations[operation_title]["value_type"] == str:
                    self.output_operations[operation_title] = None
                    self.isolate_unmatched = True
                elif self.operations[operation_title]["value_type"] == list:
                    self.output_operations[operation_title] = []
                    self.isolate_unmatched = True
                else:
                    raise ArgumentValueError(
                        f'invalid value type: "{self.operations[operation_title]["value_type"]}"'
                    )
            else:
                print(
                    f'Error: operation "{real_operation}" requires at least one argument'
                )
                raise SystemExit(1)
        else:
            print("Error: only one operation at the same time is supported")
            raise SystemExit(1)

    def __match_option(
        self, option_title: str, real_option: str, real_argument: str
    ) -> None:
        if (
            self.active_operation is not None
            and self.options[option_title]["available_with_operations"] is not None
            and self.active_operation
            not in self.options[option_title]["available_with_operations"]
        ):
            print(
                f'Error: option "{real_option}" is not available with operation "{self.active_operation}"'
            )
            raise SystemExit(1)

        elif (
            self.active_operation is not None
            and self.options[option_title]["available_with_groups"] is not None
            and self.operations[self.active_operation]["group"]
            not in self.options[option_title]["available_with_groups"]
        ):
            print(
                f'Error: option "{real_option}" is not available with operation "{self.active_operation}"'
            )
            raise SystemExit(1)

        else:
            if len(real_argument.split("=")) == 2:
                if self.options[option_title]["value_type"] == int:
                    try:
                        self.output_options[option_title] = int(
                            real_argument.split("=")[1]
                        )
                    except ValueError:
                        print(f'Error: option "{real_option}" requires an integer')
                        raise SystemExit(1)
                elif self.options[option_title]["value_type"] == str:
                    if real_argument.split("=")[1]:
                        self.output_options[option_title] = str(
                            real_argument.split("=")[1]
                        )
                    else:
                        print(
                            f'Error: option "{real_option}" requires at least one argument'
                        )
                        raise SystemExit(1)
                else:
                    print(
                        f'Error: option "{real_option}" does not support the "=" operator'
                    )
                    raise SystemExit(1)
            elif self.options[option_title]["value_type"] == bool:
                self.output_options[option_title] = True
            elif len(self.arguments) - self.arguments.index(real_argument) > 1:
                if self.options[option_title]["value_type"] == int:
                    try:
                        self.output_options[option_title] = int(
                            self.arguments[self.arguments.index(real_argument) + 1]
                        )
                    except ValueError:
                        print(f'Error: option "{real_option}" requires an integer')
                        raise SystemExit(1)
                    else:
                        self.arguments.pop(self.arguments.index(real_argument) + 1)
                elif self.options[option_title]["value_type"] == str:
                    self.output_options[option_title] = str(
                        self.arguments[self.arguments.index(real_argument) + 1]
                    )
                    self.arguments.pop(self.arguments.index(real_argument) + 1)
                elif self.options[option_title]["value_type"] == list:
                    self.output_options[option_title] = []
                    for value in self.arguments[
                        self.arguments.index(real_argument) + 1 :
                    ]:
                        if re.match(r"-[A-z\d_.\-]*", value):
                            break
                        else:
                            self.output_options[option_title].append(value)
                            self.arguments.remove(value)
                else:
                    raise ArgumentValueError(
                        f'invalid value type: "{self.options[option_title]["value_type"]}"'
                    )
            else:
                print(f'Error: option "{real_option}" requires at least one argument')
                raise SystemExit(1)

    def parse(self) -> [dict, dict]:
        """
        Parse all arguments and return matches
        :return: operations, options
        """

        # Empty the output arguments to avoid problems if this function is used multiple times
        self.output_operations = {}
        self.output_options = {}

        for argument in self.arguments:
            if argument in self.operations.keys():
                self.__match_operation(
                    operation_title=argument,
                    real_operation=argument,
                    real_argument=argument,
                )

            elif argument in self.options.keys():
                self.__match_option(
                    option_title=argument, real_option=argument, real_argument=argument
                )

            elif argument in self.short_operations.keys():
                self.__match_operation(
                    operation_title=self.short_operations[argument],
                    real_operation=argument,
                    real_argument=argument,
                )

            elif argument in self.short_options.keys():
                self.__match_option(
                    option_title=self.short_options[argument],
                    real_option=argument,
                    real_argument=argument,
                )

            elif (
                len(argument.split("=")) == 2
                and argument.split("=")[0] in self.operations.keys()
            ):
                self.__match_operation(
                    operation_title=argument.split("=")[0],
                    real_operation=argument.split("=")[0],
                    real_argument=argument,
                )

            elif (
                len(argument.split("=")) == 2
                and argument.split("=")[0] in self.options.keys()
            ):
                self.__match_option(
                    option_title=argument.split("=")[0],
                    real_option=argument.split("=")[0],
                    real_argument=argument,
                )

            elif (
                self.allow_short_args_together
                and len(argument) > 1
                and (
                    argument[0:1] in self.short_operations.keys()
                    or argument[0:2] in self.short_operations.keys()
                )
            ):
                for character in argument.replace("-", ""):
                    if (
                        character in self.short_operations.keys()
                        or f"-{character}" in self.short_operations.keys()
                    ):
                        short_argument = (
                            character
                            if character in self.short_operations.keys()
                            else f"-{character}"
                        )

                        self.__match_operation(
                            operation_title=self.short_operations[short_argument],
                            real_operation=short_argument,
                            real_argument=argument,
                        )

                    elif (
                        character in self.short_options.keys()
                        or f"-{character}" in self.short_options.keys()
                    ):
                        short_argument = (
                            character
                            if character in self.short_options.keys()
                            else f"-{character}"
                        )

                        self.__match_option(
                            option_title=self.short_options[short_argument],
                            real_option=short_argument,
                            real_argument=argument,
                        )

                    else:
                        print(f'Error: invalid argument "{character}" in "{argument}"')
                        raise SystemExit(1)

            elif (
                self.allow_short_args_together
                and len(argument) > 1
                and argument[0:2] in self.short_options.keys()
            ):
                for character in argument.replace("-", ""):
                    if (
                        character in self.short_options.keys()
                        or f"-{character}" in self.short_options.keys()
                    ):
                        short_argument = (
                            character
                            if character in self.short_options.keys()
                            else f"-{character}"
                        )

                        self.__match_option(
                            option_title=self.short_options[short_argument],
                            real_option=short_argument,
                            real_argument=argument,
                        )

                    elif (
                        character in self.short_operations.keys()
                        or f"-{character}" in self.short_operations.keys()
                    ):
                        print(
                            "Error: operation must be specified before any other arguments"
                        )
                        raise SystemExit(1)

                    else:
                        print(f'Error: invalid argument "{character}" in "{argument}"')
                        raise SystemExit(1)

            elif (
                self.isolate_unmatched
                and self.active_operation is not None
                and not re.match(r"-[A-z\d_.\-]*", argument)
                and self.operations[self.active_operation]["value_type"] == list
            ):
                self.output_operations[self.active_operation].append(argument)

            elif (
                self.isolate_unmatched
                and self.active_operation is not None
                and not re.match(r"-[A-z\d_.\-]*", argument)
                and self.operations[self.active_operation]["value_type"] == str
                and self.output_operations[self.active_operation] is None
            ):
                self.output_operations[self.active_operation] = argument

            elif (
                self.isolate_unmatched
                and self.active_operation is not None
                and not re.match(r"-[A-z\d_.\-]*", argument)
                and self.operations[self.active_operation]["value_type"] == int
                and self.output_operations[self.active_operation] is None
            ):
                try:
                    self.output_operations[self.active_operation] = int(argument)
                except ValueError:
                    print(f'Error: operation "{argument}" requires an integer')
                    raise SystemExit(1)

            else:
                print(f'Error: invalid argument "{argument}"')
                raise SystemExit(1)

        # Check if all active operations that require a list, a str or an int have at least one value
        for active_operation in self.output_operations.keys():
            if (
                self.operations[active_operation]["value_type"] == list
                and self.output_operations[active_operation] == []
            ):
                print(
                    f'Error: operation "{active_operation}" requires at least one argument'
                )
                raise SystemExit(1)
            elif (
                self.operations[active_operation]["value_type"] in (str, int)
                and self.output_operations[active_operation] is None
            ):
                print(
                    f'Error: operation "{active_operation}" requires at least one argument'
                )
                raise SystemExit(1)

        # Check if all required operations are active
        for operation in self.operations:
            if (
                self.operations[operation]["required"]
                and operation not in self.output_operations.keys()
            ):
                print(f'Error: operation "{operation}" is required')
                raise SystemExit(1)

        # Check if all required options (by an operation or by the program) are available
        for option in self.options:
            if (
                self.options[option]["required"]
                and option not in self.output_options.keys()
            ):
                print(f'Error: option "{option}" is required')
                raise SystemExit(1)
            if (
                self.options[option]["required_by_operations"] is not None
                and option not in self.output_options
            ):
                for required in self.options[option]["required_by_operations"]:
                    if required in self.output_operations.keys():
                        print(
                            f'Error: operation "{required}" requires the option "{option}"'
                        )
                        raise SystemExit(1)
            if (
                self.options[option]["required_by_groups"] is not None
                and option not in self.output_options
            ):
                for required_group in self.options[option]["required_by_groups"]:
                    for operation in self.operations:
                        if (
                            self.operations[operation]["group"] == required_group
                            and operation in self.output_operations
                        ):
                            print(
                                f'Error: operation "{operation}" requires the option "{option}"'
                            )
                            raise SystemExit(1)

        # Check if at least one operation is specified
        if self.output_operations == {} and self.one_operation_required:
            print("Error: one operation is required")
            raise SystemExit(1)

        # Set all the unused arguments to False or None
        for operation in self.operations:
            if operation not in self.output_operations:
                self.output_operations[operation] = self.operations[operation][
                    "default_value"
                ]

        for option in self.options:
            if option not in self.output_options:
                self.output_options[option] = self.options[option]["default_value"]

        return self.output_operations, self.output_options
