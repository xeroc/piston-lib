from grapheneapi.graphenewsrpc import GrapheneWebsocketRPC
import threading
from websocket import create_connection
import json
import time
import logging
log = logging.getLogger("grapheneapi.steemnoderpc")


class RPCError(Exception):
    pass


class SteemNodeRPC(GrapheneWebsocketRPC):
    """ This class allows to call API methods synchronously, without
        callbacks. It logs in and registers to the APIs:

        * database
        * history

        :param str url: Websocket URL
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
                 url,
                 user="",
                 password="",
                 apis=["database",
                       "network_broadcast"]):
        self.apis = apis
        super(SteemNodeRPC, self).__init__(url, user, password)

    def register_apis(self):
        for api in self.apis:
            api = api.replace("_api", "")
            self.api_id[api] = self.get_api_by_name("%s_api" % api, api_id=1)
            if not self.api_id[api] and not isinstance(self.api_id[api], int):
                log.info("No permission to access %s API. " % api)

    def get_account(self, name):
        return self.get_accounts([name])[0]

    def get_asset(self, name):
        raise NotImplementedError  # We overwrite this method from grapehenlib

    def getFullAccountHistory(self, account, begin=1, limit=100, sort="block"):
        raise NotImplementedError  # We overwrite this method from grapehenlib

    def get_object(self, o):
        raise NotImplementedError  # We overwrite this method from grapehenlib

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
                yield self.get_block(blocknum)

            # Set new start
            start = head_block + 1

            # Sleep for one block
            time.sleep(block_interval)

    def stream(self, opName, *args, **kwargs):
        """ Yield specific operations (e.g. comments) only

            :param str opName: Name of the operation, e.g. vote,
                                comment, transfer, transfer_to_vesting,
                                withdraw_vesting, limit_order_create,
                                limit_order_cancel, feed_publish,
                                convert, account_create, account_update,
                                witness_update, account_witness_vote,
                                account_witness_proxy, pow, custom,
                                report_over_production,
                                fill_convert_request, comment_reward,
                                curate_reward, liquidity_reward,
                                interest, fill_vesting_withdraw,
                                fill_order,
            :param int start: Begin at this block
        """
        for block in self.block_stream(*args, **kwargs):
            if not len(block["transactions"]):
                continue
            for tx in block["transactions"]:
                for op in tx["operations"]:
                    if op[0] == opName:
                        yield op[1]
