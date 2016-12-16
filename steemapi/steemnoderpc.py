import re
from grapheneapi.graphenewsrpc import GrapheneWebsocketRPC
import threading
from websocket import create_connection
import json
import time
from . import exceptions
from .exceptions import NoAccessApi, RPCError
import logging
log = logging.getLogger("grapheneapi.steemnoderpc")


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

    def register_apis(self):
        for api in self.apis:
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
        """ Returns a generator for individual account transactions. The
            latest operation will be first. This call can be used in a
            ``for`` loop.

            :param str account: account name to get history for
            :param int first: sequence number of the first transaction to return
            :param int limit: limit number of transactions to return
            :param array only_ops: Limit generator by these operations
        """
        cnt = 0
        _limit = 100
        if _limit > first:
            _limit = first
        while first > 0:
            # RPC call
            txs = self.get_account_history(account, first, _limit)
            for i in txs[::-1]:
                if exclude_ops and i[1]["op"][0] in exclude_ops:
                    continue
                if not only_ops or i[1]["op"][0] in only_ops:
                    cnt += 1
                    yield i
                    if limit >= 0 and cnt >= limit:
                        break
            if limit >= 0 and cnt >= limit:
                break
            if len(txs) < _limit:
                break
            first = txs[0][0] - 1  # new first
            if _limit > first:
                _limit = first

    def block_stream(self, start=None, mode="irreversible"):
        """ Yields blocks starting from ``start``.

            :param int start: Starting block
            :param str mode: We here have the choice between
                 * "head": the last block
                 * "irreversible": the block that is confirmed by 2/3 of all block producers and is thus irreversible!
        """
        # Let's find out how often blocks are generated!
        config = self.get_config()
        block_interval = config["STEEMIT_BLOCK_INTERVAL"]

        if not start:
            props = self.get_dynamic_global_properties()
            # Get block number
            if mode == "head":
                start = props['head_block_number']
            elif mode == "irreversible":
                start = props['last_irreversible_block_num']
            else:
                raise ValueError(
                    '"mode" has to be "head" or "irreversible"'
                )

        # We are going to loop indefinitely
        while True:

            # Get chain properies to identify the
            # head/last reversible block
            props = self.get_dynamic_global_properties()

            # Get block number
            if mode == "head":
                head_block = props['head_block_number']
            elif mode == "irreversible":
                head_block = props['last_irreversible_block_num']
            else:
                raise ValueError(
                    '"mode" has to be "head" or "irreversible"'
                )

            # Blocks from start until head block
            for blocknum in range(start, head_block + 1):
                # Get full block
                block = self.get_block(blocknum)
                block.update({"block_num": blocknum})
                yield block

            # Set new start
            start = head_block + 1

            # Sleep for one block
            time.sleep(block_interval)

    def stream(self, opNames, *args, **kwargs):
        """ Yield specific operations (e.g. comments) only

            :param array opNames: List of operations to filter for, e.g.
                vote, comment, transfer, transfer_to_vesting,
                withdraw_vesting, limit_order_create, limit_order_cancel,
                feed_publish, convert, account_create, account_update,
                witness_update, account_witness_vote, account_witness_proxy,
                pow, custom, report_over_production, fill_convert_request,
                comment_reward, curate_reward, liquidity_reward, interest,
                fill_vesting_withdraw, fill_order,
            :param int start: Begin at this block
        """
        if isinstance(opNames, str):
            opNames = [opNames]
        for block in self.block_stream(*args, **kwargs):
            if "transactions" not in block:
                continue
            for tx in block["transactions"]:
                for op in tx["operations"]:
                    if op[0] in opNames:
                        yield op[1]

    def list_accounts(self, start=None, step=1000, limit=None):
        """ Yield list of user accounts in alphabetical order

        :param str start: Name of account, which should be yield first
        :param int step: Describes how many accounts should be fetched in each rpc request
        :param int limit: Limit number of returned user accounts
        """
        if limit and limit < step:
            step = limit

        number_of_fetched_users = 0
        progress = step

        while progress == step and (not limit or number_of_fetched_users < limit):
            users = self.lookup_accounts(start, step)
            progress = len(users)

            if progress > 0:
                yield from users
                number_of_fetched_users += progress

                # concatenate last fetched account name with lowest possible
                # ascii character to get next lowest possible login as lower_bound
                start = users[-1] + '\0'

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
            msg = exceptions.decodeBroadcasetErrorMsg(e)
            if msg == "Account already transacted this block.":
                raise exceptions.AlreadyTransactedThisBlock(msg)
            elif msg == "Voting weight is too small, please accumulate more voting power or steem power.":
                raise exceptions.VoteWeightTooSmall(msg)
            elif msg == "Can only vote once every 3 seconds.":
                raise exceptions.OnlyVoteOnceEvery3Seconds(msg)
            elif msg == "You have already voted in a similar way.":
                raise exceptions.AlreadyVotedSimilarily(msg)
            elif re.match("^no method with name.*", msg):
                raise exceptions.NoMethodWithName(msg)
            else:
                raise e
        except Exception as e:
            raise e

    def __getattr__(self, name):
        """ Map all methods to RPC calls and pass through the arguments.
            It makes use of the GrapheneRPC library.
        """
        return super(SteemNodeRPC, self).__getattr__(name)
