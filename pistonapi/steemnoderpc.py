import re
import time
from . import exceptions
from pistonbase.chains import known_chains
from .steemwsrpc import SteemWSRPC
from .steemhttprpc import SteemHTTPRPC
from .exceptions import NoAccessApi, RPCError
import logging
import warnings
warnings.filterwarnings('default', module=__name__)
log = logging.getLogger(__name__)


class SteemNodeRPC(SteemHTTPRPC, SteemWSRPC):
    """ This class deals with the connection to the API. Either it is a
        websocket connection straight to the backend, or to a jussi
        proxy.

        :param str urls: Either a single Websocket URL, or a list of URLs
        :param str user: Username for Authentication
        :param str password: Password for Authentication

        Usage:

        .. code-block:: python

            ws = SteemNodeRPC("ws://10.0.0.16:8090")
            print(ws.get_account_count())

    """
    call_id = 0
    api_id = {}

    def __init__(self,
                 urls,
                 user="",
                 password="",
                 **kwargs):
        self.apis = kwargs.pop(
            "apis",
            ["database", "network_broadcast"]
        )
        self._urls = urls
        self.rpc.__init__(self, self._urls, **kwargs)
        self.chain_params = self.get_network()

    @property
    def rpc(self):
        if isinstance(self._urls, (list, set)):
            first_url = self._urls[0]
        else:
            first_url = self._urls

        if first_url[:2] == "ws":
            # Websocket connection
            return SteemWSRPC
        else:
            # RPC/HTTP connection
            return SteemHTTPRPC

    def get_account(self, name):
        account = self.get_accounts([name])
        if account:
            return account[0]

    def account_history(self, account, first=99999999999,
                        limit=-1, only_ops=[], exclude_ops=[]):
        warnings.warn(
            "The block_stream() call has been moved to `steem.account.Account.rawhistory()`",
            DeprecationWarning
        )
        from piston.account import Account
        return Account(account, steem_instance=self.steem).rawhistory(
            first=first, limit=limit,
            only_ops=only_ops,
            exclude_ops=exclude_ops)

    def block_stream(self, start=None, stop=None, mode="irreversible"):
        warnings.warn(
            "The block_stream() call has been moved to `steem.blockchain.Blockchain.blocks()`",
            DeprecationWarning
        )
        from piston.blockchain import Blockchain
        return Blockchain(mode=mode).blocks(start, stop)

    def stream(self, opNames, *args, **kwargs):
        warnings.warn(
            "The stream() call has been moved to `steem.blockchain.Blockchain.stream()`",
            DeprecationWarning
        )
        from piston.blockchain import Blockchain
        return Blockchain(mode=kwargs.get("mode", "irreversible")).stream(opNames, *args, **kwargs)

    def list_accounts(self, start=None, step=1000, limit=None, **kwargs):
        warnings.warn(
            "The list_accounts() call has been moved to `steem.blockchain.Blockchain.get_all_accounts()`",
            DeprecationWarning
        )
        from piston.blockchain import Blockchain
        return Blockchain(mode=kwargs.get("mode", "irreversible")).get_all_accounts(start=start, steps=step, **kwargs)

    def get_network(self):
        """ Identify the connected network. This call returns a
            dictionary with keys chain_id, prefix, and other chain
            specific settings
        """
        props = self.get_dynamic_global_properties()
        chain = props["current_supply"].split(" ")[1]
        assert chain in known_chains, "The chain you are connecting to is not supported"
        return known_chains.get(chain)

    def rpcexec(self, payload):
        """ Execute a call by sending the payload.
            It makes use of the GrapheneRPC library.
            In here, we mostly deal with Steem specific error handling

            :param json payload: Payload data
            :raises ValueError: if the server does not respond in proper JSON format
            :raises RPCError: if the server returns an error
        """
        try:
            return self.rpc.rpcexec(self, payload)
        except RPCError as e:
            msg = exceptions.decodeRPCErrorMsg(e).strip()
            if msg == "Account already transacted this block.":
                raise exceptions.AlreadyTransactedThisBlock(msg)
            elif msg == "missing required posting authority":
                raise exceptions.MissingRequiredPostingAuthority
            elif msg == "Voting weight is too small, please accumulate more voting power or steem power.":
                raise exceptions.VoteWeightTooSmall(msg)
            elif msg == "Can only vote once every 3 seconds.":
                raise exceptions.OnlyVoteOnceEvery3Seconds(msg)
            elif msg == "You have already voted in a similar way.":
                raise exceptions.AlreadyVotedSimilarily(msg)
            elif msg == "You may only post once every 5 minutes.":
                raise exceptions.PostOnlyEvery5Min(msg)
            elif msg == "Duplicate transaction check failed":
                raise exceptions.DuplicateTransaction(msg)
            elif msg == "Account exceeded maximum allowed bandwidth per vesting share.":
                raise exceptions.ExceededAllowedBandwidth(msg)
            elif re.match("^no method with name.*", msg):
                raise exceptions.NoMethodWithName(msg)
            elif msg:
                raise exceptions.UnhandledRPCError(msg)
            else:
                raise e
        except Exception as e:
            raise e

    def __getattr__(self, name):
        """ Map all methods to RPC calls and pass through the arguments.
            It makes use of the GrapheneRPC library.
        """
        return self.rpc.__getattr__(self, name)
