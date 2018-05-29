class MissingCommandError(Exception):
    """ Indicates a required CLI command is missing """


class FailedAction(Exception):
    """ Indicates a specific action failed """


class InvalidAction(Exception):
    """ Indicates a specific action failed """
