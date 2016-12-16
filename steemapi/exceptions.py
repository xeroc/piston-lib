import re
from grapheneapi.graphenewsrpc import RPCError


def decodeRPCErrorMsg(e):
    """ Helper function to decode the raised Exception and give it a
        python Exception class
    """
    found = re.search(
        (
            "10 assert_exception: Assert Exception\n"
            ".*: (.*)\n"
        ),
        str(e),
        flags=re.M)
    if found:
        return found.group(1).strip()
    else:
        return str(e)


class NoAccessApi(RPCError):
    pass


class AlreadyTransactedThisBlock(RPCError):
    pass


class VoteWeightTooSmall(RPCError):
    pass


class OnlyVoteOnceEvery3Seconds(RPCError):
    pass


class AlreadyVotedSimilarily(RPCError):
    pass


class NoMethodWithName(RPCError):
    pass


class PostOnlyEvery5Min(RPCError):
    pass
