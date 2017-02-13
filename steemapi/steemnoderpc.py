import re
import time
from . import exceptions
from .exceptions import NoAccessApi, RPCError
from grapheneapi.graphenewsrpc import GrapheneWebsocketRPC
from steembase.chains import known_chains
import logging
import warnings
warnings.filterwarnings('default', module=__name__)
log = logging.getLogger(__name__)


class SteemNodeRPC(GrapheneWebsocketRPC):
    """ This class allows to call API methods synchronously, without
        callbacks. It logs in and registers to the APIs:

        * database
        * history

        :param str urls: Either a single Websocket URL, or a list of URLs
        :param str user: Username for Authentication
        :param str password: Password for Authentication
        :param Array apis: List of APIs to register to (default: ["database", "network_broadcast"])

        Available APIs

              * database
              * network_node
              * network_broadcast
              * history

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
        super(SteemNodeRPC, self).__init__(urls, user, password, **kwargs)
        self.chain_params = self.get_network()

    def register_apis(self, apis=None):
        for api in (apis or self.apis):
            api = api.replace("_api", "")
            self.api_id[api] = self.get_api_by_name("%s_api" % api, api_id=1)
            if not self.api_id[api] and not isinstance(self.api_id[api], int):
                raise NoAccessApi("No permission to access %s API. " % api)

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
        from steem.account import Account
        return Account(account, steem_instance=self.steem).rawhistory(
            first=first, limit=limit,
            only_ops=only_ops,
            exclude_ops=exclude_ops)

    def block_stream(self, start=None, stop=None, mode="irreversible"):
        warnings.warn(
            "The block_stream() call has been moved to `steem.blockchain.Blockchain.blocks()`",
            DeprecationWarning
        )
        from steem.blockchain import Blockchain
        return Blockchain(mode=mode).blocks(start, stop)

    def stream(self, opNames, *args, **kwargs):
        warnings.warn(
            "The stream() call has been moved to `steem.blockchain.Blockchain.stream()`",
            DeprecationWarning
        )
        from steem.blockchain import Blockchain
        return Blockchain(mode=kwargs.get("mode", "irreversible")).stream(opNames, *args, **kwargs)

    def list_accounts(self, start=None, step=1000, limit=None, **kwargs):
        warnings.warn(
            "The list_accounts() call has been moved to `steem.blockchain.Blockchain.get_all_accounts()`",
            DeprecationWarning
        )
        from steem.blockchain import Blockchain
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
            # Forward call to GrapheneWebsocketRPC and catch+evaluate errors
            return super(SteemNodeRPC, self).rpcexec(payload)
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
        return super(SteemNodeRPC, self).__getattr__(name)
