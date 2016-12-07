try:
    import asyncio
except ImportError:
    raise ImportError("Missing dependency: asyncio")
try:
    import yaml
except ImportError:
    raise ImportError("Missing dependency: asyncio")

import websockets
import json

""" Error Classes """


class ConfigError(Exception):
    pass


class RPCServerError(Exception):
    pass


class RPCClientError(Exception):
    pass


""" Config class """


class Config():
    """ The ``Config`` class is used to contain all the parameters needed by ``SteemAsyncClient`` in
        a neat and simple object. The main parameters needed are the witness connection parameters and
        the mapping of aliases used in code to Steem APIs that are requested to be initialized by
        ``SteemAsyncClient`` on behalf of the code.

        The simplest way to create a valid ``Config`` object is to pass the keyword arguments to the
        constructor to initialize the relevant parameters, as the following example demonstrates:

        .. code-block:: python

          config = Config(witness_url      = "ws://localhost:8090/",
                          witness_user     = "",
                          witness_password = "",
                          witness_apis     = {"db": "database",
                                              "broadcast": "network_broadcast"},
                          wallet_url       = "ws://localhost:8091/",
                          wallet_user      = "",
                          wallet_password  = "")

        But the better way to create the ``Config`` object is to put the parameters in YAML
        configuration file and load it as in the following example:

        .. code-block:: python

          config = Config(config_file = "/path/to/config.yml")

        Note that you can combine both methods by specifying a ``config_file`` but then selectively
        overriding any of the paramaters from the configuration file by specifying them directly
        as keyword arguments to the Config constructor.
    """
    def __init__(self, **kwargs):
        witness_url_specified = False
        wallet_url_specified = False
        if "config_file" in kwargs:
            # Load paramaters from YAML configuration file
            with open(kwargs["config_file"]) as f:
                contents = f.read()
            c = yaml.safe_load(contents)
            if "witness" in c:
                self.witness = c["witness"]
                if "url" in self.witness and self.witness["url"]:
                    witness_url_specified = True
                if ("user" not in self.witness) or (not self.witness["user"]):
                    self.witness["user"] = ""
                if ("password" not in self.witness) or (not self.witness["password"]):
                    self.witness["password"] = ""
                if ("apis" not in self.witness) or (not self.witness["apis"]):
                    self.witness["apis"] = {}
                elif not isinstance(self.witness["apis"], (dict, list)):
                    raise ConfigError("Witness paramater apis not properly specified in configuration file")
            if "wallet" in c:
                self.wallet = c["wallet"]
                if "url" in self.wallet and self.wallet["url"]:
                    wallet_url_specified = True
                if ("user" not in self.wallet) or (not self.wallet["user"]):
                    self.wallet["user"] = ""
                if ("password" not in self.wallet) or (not self.wallet["password"]):
                    self.wallet["password"] = ""
            if ("witness" not in c) and ("wallet" not in c):
                raise ConfigError("At least either witness or wallet parameters must be specified in configuration file")

        if (not witness_url_specified) and ("witness_url" in kwargs):
            witness_url_specified = True
            self.witness = {"url": kwargs["witness_url"], "user": "", "password": "", "apis": {}}
        if (not wallet_url_specified) and ("wallet_url" in kwargs):
            wallet_url_specified = True
            self.wallet = {"url": kwargs["wallet_url"], "user": "", "password": ""}
        if not (witness_url_specified or wallet_url_specified):
            raise ConfigError("At least either witness or wallet parameters must be specified")

        if witness_url_specified:
            if "witness_user" in kwargs:
                self.witness["user"] = kwargs["witness_user"]
            if "witness_password" in kwargs:
                self.witness["password"] = kwargs["witness_password"]
            if "witness_apis" in kwargs:
                if not isinstance(kwargs["witness_apis"], (dict, list)):
                    raise ConfigError("Witness parameter apis not properly specified")
                self.witness["apis"] = kwargs["witness_apis"]
            if not isinstance(self.witness["apis"], dict):
                apis = self.witness["apis"]
                self.witness["apis"] = {}
                for api_name in apis:
                    self.witness["apis"][api_name] = api_name
            for (alias, api_name) in self.witness["apis"].items():
                if not isinstance(alias, str):
                    raise ConfigError("Invalid alias specified in witness apis")
                if not isinstance(api_name, str):
                    raise ConfigError("Invalid API name specified in witness apis")
                if alias[0] == '_':
                    raise ConfigError("Alias specified in witness apis starts with _ which is not allowed")
                elif alias == "run":
                    raise ConfigError("Alias 'run' specified in witness apis which is a reserved word")
                elif alias == "wallet":
                    raise ConfigError("Alias 'wallet' specified in witness apis which is a reserved word")
        if wallet_url_specified:
            if "wallet_user" in kwargs:
                self.wallet["user"] = kwargs["wallet_user"]
            if "wallet_password" in kwargs:
                self.wallet["password"] = kwargs["wallet_password"]


""" API class """


class SteemAsyncClient(object):
    """ Steem Asynchronous Client

        The ``SteemAsyncClient`` class is an abstraction layer that makes asynchronous
        use of the RPC API of either steemd (witness) or cli_wallet (wallet)  easy to use.

        :param class config: the configuration class

        Example usage of this class:

        .. code-block:: python

            from steemasyncclient import SteemAsyncClient, Config

            @asyncio.coroutine
            def print_block_number(steem):
               res = yield from steem.database.get_dynamic_global_properties()
               print(res["head_block_number"])

            steem = SteemAsyncClient(Config(witness_url="ws://localhost:8090",
                                            witness_apis=["database"]))
            steem.run([print_block_number])

        See more examples of how to use this class in the examples folder.
    """

    def __init__(self, config):
        self._config = config
        self._api_map = {"login": "login"}
        self._api_id = {"login": 1}
        self._witness_call_id = 0
        self._wallet_call_id = 0
        self._witness_pending_rpc = {}
        self._wallet_pending_rpc = {}
        self._witness_ws = None
        self._wallet_ws = None
        if hasattr(config, "wallet"):
            self.wallet = SteemAsyncClient.WalletRPCDispatch(self)

    class WalletRPCDispatch(object):
        # Internal implementation specific class. Users of SteemAsyncClient do not need to use this class.
        def __init__(self, steem):
            self._steem = steem

        def __getattr__(self, method_name):
            """ Map field names to Steem wallet methods
            """
            if method_name[0] == '_':
                raise RPCClientError("RPC call method name starts with _ which is not allowed")

            @asyncio.coroutine
            def method(*args, **kwargs):
                call_id = self._steem._wallet_call_id
                self._steem._wallet_call_id += 1
                query = {"jsonrpc": "2.0", "id": call_id, "method": method_name, "params": args}
                self._steem._wallet_pending_rpc[call_id] = asyncio.Future()
                yield from self._steem._wallet_ws.send(json.dumps(query))
                if "future" in kwargs and kwargs["future"]:
                    return self._steem._wallet_pending_rpc[call_id]
                else:
                    ret = yield from self._steem._wallet_pending_rpc[call_id]
                    return ret
            return method

    class WitnessRPCDispatch(object):
        # Internal implementation specific class. Users of SteemAsyncClient do not need to use this class.
        def __init__(self, steem, api_id):
            self._steem = steem
            self._api_id = api_id

        def __getattr__(self, method_name):
            """ Map field names to Steem methods within the specific Steem API that this
                object is assigned to.
            """
            if method_name[0] == '_':
                raise RPCClientError("RPC call method name starts with _ which is not allowed")

            @asyncio.coroutine
            def method(*args, **kwargs):
                call_id = self._steem._witness_call_id
                self._steem._witness_call_id += 1
                query = {"jsonrpc": "2.0", "id": call_id, "method": "call", "params": [self._api_id, method_name, args]}
                self._steem._witness_pending_rpc[call_id] = asyncio.Future()
                yield from self._steem._witness_ws.send(json.dumps(query))
                if "future" in kwargs and kwargs["future"]:
                    return self._steem._witness_pending_rpc[call_id]
                else:
                    ret = yield from self._steem._witness_pending_rpc[call_id]
                    return ret
            return method

    def __getattr__(self, api_name):
        """ Map field names to Steem APIs using the map provided in Config.
        """
        if api_name == "wallet":
            raise RPCClientError("Wallet RPC was not specified when initializing SteemAsyncClient")
        if not self._witness_ws:
            raise RPCClientError("Witness RPC was not specified when initializing SteemAsyncClient")
        if api_name in self._api_map and self._api_map[api_name] in self._api_id:
            api_id = self._api_id[self._api_map[api_name]]
        else:
            raise RPCClientError("Have not registered an API with alias '{}'".format(api_name))
        return SteemAsyncClient.WitnessRPCDispatch(self, api_id)

    @asyncio.coroutine
    def _initialize(self, coroutines):
        if self._witness_ws:
            l = yield from self.login.login(self._config.witness["user"], self._config.witness["password"])
            if not l:
                raise RPCClientError("Could not login to steemd node")
            for (alias, api_name) in self._config.witness["apis"].items():
                api_id = yield from self.login.get_api_by_name("{}_api".format(api_name))
                if not api_id:
                    raise RPCClientError("Could not acquire {}_api".format(api_name))
                self._api_id[api_name] = api_id
                self._api_map[alias] = api_name
        futures = []
        for c in coroutines:
            futures.append(asyncio.async(c(self)))
        yield from asyncio.wait(futures)

    @asyncio.coroutine
    def _handle(self, coroutines):
        if hasattr(self._config, "wallet"):
            self._wallet_ws = yield from websockets.connect(self._config.wallet["url"])
            wallet_ws_recv_task = asyncio.async(self._wallet_ws.recv())
        if hasattr(self._config, "witness"):
            self._witness_ws = yield from websockets.connect(self._config.witness["url"])
            witness_ws_recv_task = asyncio.async(self._witness_ws.recv())
        try:
            main_task = asyncio.async(self._initialize(coroutines))
            while True:
                tasks = [main_task]
                if hasattr(self._config, "wallet"):
                    tasks.append(wallet_ws_recv_task)
                if hasattr(self._config, "witness"):
                    tasks.append(witness_ws_recv_task)

                done, pending = yield from asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                if main_task in done:
                    if hasattr(self._config, "wallet"):
                        wallet_ws_recv_task.cancel()
                        self._wallet_pending_rpc = {}
                    if hasattr(self._config, "witness"):
                        witness_ws_recv_task.cancel()
                        self._witness_pending_rpc = {}
                    break

                if hasattr(self._config, "wallet") and wallet_ws_recv_task in done:
                    try:
                        r = json.loads(wallet_ws_recv_task.result())
                    except ValueError:
                        raise RPCClientError("Wallet server returned invalid format via websocket. Expected JSON!")
                    call_id = r["id"]
                    if call_id in self._wallet_pending_rpc:
                        future = self._wallet_pending_rpc[call_id]
                        del self._wallet_pending_rpc[call_id]
                        if "error" in r:
                            if "detail" in r["error"]:
                                future.set_exception(RPCServerError(r["error"]["detail"]))
                            else:
                                future.set_exception(RPCServerError(r["error"]["message"]))
                        future.set_result(r["result"])
                    else:
                        raise RPCClientError("Not expecting a response via websocket from wallet server with call id {}".format(call_id))
                    wallet_ws_recv_task = asyncio.async(self._wallet_ws.recv())

                if hasattr(self._config, "witness") and witness_ws_recv_task in done:
                    try:
                        r = json.loads(witness_ws_recv_task.result())
                    except ValueError:
                        raise RPCClientError("Witness server returned invalid format via websocket. Expected JSON!")
                    call_id = r["id"]
                    if call_id in self._witness_pending_rpc:
                        future = self._witness_pending_rpc[call_id]
                        del self._witness_pending_rpc[call_id]
                        if "error" in r:
                            if "detail" in r["error"]:
                                future.set_exception(RPCServerError(r["error"]["detail"]))
                            else:
                                future.set_exception(RPCServerError(r["error"]["message"]))
                        future.set_result(r["result"])
                    else:
                        raise RPCClientError("Not expecting a response via websocket from witness server with call id {}".format(call_id))
                    witness_ws_recv_task = asyncio.async(self._witness_ws.recv())

        finally:
            if hasattr(self._config, "wallet"):
                yield from self._wallet_ws.close()
            if hasattr(self._config, "witness"):
                yield from self._witness_ws.close()

    def run(self, coroutines):
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(self._handle(coroutines))
        finally:
            pass  # loop.close()
