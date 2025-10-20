# argumentor - A simple, copylefted, lightweight library to work with command-line arguments in Python
# Licensed under LGPLv3
# Copyright (C) 2021-2022 Twann <tw4nn@disroot.org>


class ExecNameError(IOError):
    def __init__(self, *args):
        super(ExecNameError, self).__init__(*args)


class OperationExistsError(IOError):
    def __init__(self, *args):
        super(OperationExistsError, self).__init__(*args)


class OptionExistsError(IOError):
    def __init__(self, *args):
        super(OptionExistsError, self).__init__(*args)


class InvalidOptionError(IOError):
    def __init__(self, *args):
        super(InvalidOptionError, self).__init__(*args)


class InvalidOperationError(IOError):
    def __init__(self, *args):
        super(InvalidOperationError, self).__init__(*args)


class ArgumentValueError(IOError):
    def __init__(self, *args):
        super(ArgumentValueError, self).__init__(*args)


class GroupExistsError(IOError):
    def __init__(self, *args):
        super(GroupExistsError, self).__init__(*args)


class GroupNotExistsError(IOError):
    def __init__(self, *args):
        super(GroupNotExistsError, self).__init__(*args)
