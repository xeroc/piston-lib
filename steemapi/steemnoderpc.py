import threading
from websocket import create_connection
import json
import time


class RPCError(Exception):
    pass


class SteemNodeRPC(object):
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

        .. note:: This class allows to call methods available via
                  websocket. If you want to use the notification
                  subsystem, please use ``SteemWebsocket`` instead.

    """
    call_id = 0
    api_id = {}

    def __init__(self,
                 url,
                 user="",
                 password="",
                 apis=["database",
                       "network_broadcast"]):
        self.url = url
        self.user = user
        self.password = password
        self.apis = apis

        self.connect()

    def connect(self):
        self.ws = create_connection(self.url)
        self.login(self.user, self.password, api_id=1)

        for api in self.apis:
            api = api.replace("_api", "")
            self.api_id[api] = self.get_api_by_name("%s_api" % api, api_id=1)
            if not self.api_id[api]:
                print("[Warning] No permission to access %s API. " % api +
                      "The library may not function as desired!")

    def get_call_id(self):
        """ Get the ID for the next RPC call """
        self.call_id += 1
        return self.call_id

    def get_account(self, name):
        return self.get_accounts([name])[0]

    def get_object(self, o):
        return self.get_objects([o])[0]

    def rpcexec(self, payload):
        """ Execute a call by sending the payload

            :param json payload: Payload data
            :raises ValueError: if the server does not respond in proper JSON format
            :raises RPCError: if the server returns an error
        """
        try:
            try:
                self.ws.send(json.dumps(payload))
            except:
                # retry after reconnect
                try:
                    self.ws.close()
                finally:
                    self.connect()
                self.ws.send(json.dumps(payload))

            ret = json.loads(self.ws.recv())
            if 'error' in ret:
                if 'detail' in ret['error']:
                    raise RPCError(ret['error']['detail'])
                else:
                    raise RPCError(ret['error']['message'])
        except ValueError:
            raise ValueError("Client returned invalid format. Expected JSON!")
        except RPCError as err:
            raise err
        else:
            return ret["result"]

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
            start = head_block

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

    def __getattr__(self, name):
        """ Map all methods to RPC calls and pass through the arguments
        """
        def method(*args, **kwargs):
            if "api_id" not in kwargs :
                if ("api" in kwargs and kwargs["api"] in self.api_id) :
                    api_id = self.api_id[kwargs["api"]]
                else:
                    api_id = 0
            else:
                api_id = kwargs["api_id"]
            query = {"method": "call",
                     "params": [api_id, name, args],
                     "jsonrpc": "2.0",
                     "id": 0}
            r = self.rpcexec(query)
            return r
        return method
