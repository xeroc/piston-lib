class AccountExistsException(Exception):
    pass


class AccountDoesNotExistsException(Exception):
    pass


class InsufficientAuthorityError(Exception):
    pass


class MissingKeyError(Exception):
    pass
