from pistonapi.steemwalletrpc import SteemWalletRPC
from pistonapi.steemnoderpc import SteemNodeRPC

import logging as log


class ExampleConfig():
    """ The behavior of your program (e.g. reactions on messages) can be
        defined in a separated class (here called ``Config()``. It contains
        the wallet and witness connection parameters:

        The config class is used to define several attributes *and*
        methods that will be used during API communication. This is
        particularily useful when dealing with event-driven websocket
        notifications.

        **RPC-Only Connections**:

        The simples setup for this class is a simply RPC:

        .. code-block:: python

            class Config():
                wallet_host           = "localhost"
                wallet_port           = 8092
                wallet_user           = ""
                wallet_password       = ""

        and allows the use of rpc commands similar to the
        ``SteemWalletRPC`` class:

        .. code-block:: python

            steem = SteemClient(Config)
            print(steem.rpc.info())
            print(steem.rpc.get_account("init0"))
            print(steem.rpc.get_asset("USD"))

        All methods within ``steem.rpc`` are mapped to the corresponding
        RPC call **of the wallet** and the parameters are handed over
        directly.

        **Additional Websocket Connections**:

        .. code-block:: python

            class Config():  ## Note the dependency
                wallet_host           = "localhost"
                wallet_port           = 8092
                wallet_user           = ""
                wallet_password       = ""
                witness_url           = "ws://localhost:8090/"
                witness_user          = ""
                witness_password      = ""

        All methods within ``steem.ws`` are mapped to the corresponding
        RPC call of the **full/witness node** and the parameters are handed
        over directly.

    """

    #: Wallet connection parameters
    wallet_host = "localhost"
    wallet_port = 8092
    wallet_user = ""
    wallet_password = ""

    #: Witness connection parameter
    witness_url = "ws://localhost:8090/"
    witness_user = ""
    witness_password = ""


class SteemClient():
    """ The ``SteemClient`` class is an abstraction layer that makes the use of the
        RPC and the websocket interface easier to use. A part of this
        abstraction layer is to simplyfy the usage of objects and have
        an internal objects map updated to reduce unecessary queries
        (for enabled websocket connections). Advanced developers are of
        course free to use the underlying API classes instead as well.

        :param class config: the configuration class

        If a websocket connection is configured, the websocket subsystem
        can be run by:

        .. code-block:: python

            steem = SteemClient(config)
            steem.run()

    """
    wallet_host = None
    wallet_port = None
    wallet_user = None
    wallet_password = None
    witness_url = None
    witness_user = None
    witness_password = None
    prefix = None

    #: RPC connection to the cli-wallet
    rpc = None
    wallet = None

    #: Websocket connection to the witness/full node
    ws = None
    node = None

    def __init__(self, config, **kwargs):
        """ Initialize configuration
        """
        available_features = dir(config)

        if ("wallet_host" in available_features and
                "wallet_port" in available_features):
            self.wallet_host = config.wallet_host
            self.wallet_port = config.wallet_port

            if ("wallet_user" in available_features and
                    "wallet_password" in available_features):
                self.wallet_user = config.wallet_user
                self.wallet_password = config.wallet_password

            self.rpc = SteemWalletRPC(self.wallet_host,
                                      self.wallet_port,
                                      self.wallet_user,
                                      self.wallet_password)

            # Make a reference to 'wallet'
            self.wallet = self.rpc

        # Connect to Witness Node
        if "witness_url" in available_features:
            self.witness_url = config.witness_url

            if ("witness_user" in available_features):
                self.witness_user = config.witness_user

            if ("witness_password" in available_features):
                self.witness_password = config.witness_password

            self.ws = SteemNodeRPC(self.witness_url,
                                   self.witness_user,
                                   self.witness_password,
                                   **kwargs)

            # Make a reference to 'node'
            self.node = self.ws

    def getObject(self, oid):
        return NotImplementedError
