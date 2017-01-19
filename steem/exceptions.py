class AccountExistsException(Exception):
    pass


class AccountDoesNotExistsException(Exception):
    pass


class InsufficientAuthorityError(Exception):
    pass


class MissingKeyError(Exception):
    pass


class BlockDoesNotExistsException(Exception):
    pass


class WitnessDoesNotExistsException(Exception):
    pass


class InvalidKeyFormat(Exception):
    pass


class NoWallet(Exception):
    pass


class InvalidWifError(Exception):
    pass


class WalletExists(Exception):
    pass


class PostDoesNotExist(Exception):
    pass


class VotingInvalidOnArchivedPost(Exception):
    pass
