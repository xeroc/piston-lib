from steemapi.steemclient import SteemClient
from steembase import transactions
from steembase.account import PrivateKey

from datetime import datetime
import time
import math
from . import deep_eq
import logging
import random
log = logging.getLogger(__name__)


class InvalidWifKey(Exception):
    pass


class WifNotActive(Exception):
    pass


class ExampleConfig() :
    """ The behavior of your program can be
        defined in a separated class (here called ``ExampleConfig()``. It
        contains the wallet and witness connection parameters:

        Configuration Rules:

        * `witness_url` is required in all cases
        * Either you provide access to a cli_wallet via `wallet_host`
          (etc.) or your need to provide the **active private key** to the
          account as `wif`

        The config class is used to define several attributes *and*
        methods that will be used during API communication..

        .. code-block:: python

            class Config():
                wallet_host           = "localhost"
                wallet_port           = 8092
                wallet_user           = ""
                wallet_password       = ""
                witness_url           = "ws://localhost:8090/"
                witness_user          = ""
                witness_password      = ""
                wif                   = None

        All methods within ``steem.rpc`` are mapped to the
        corresponding RPC call of the **wallet** and the parameters are
        handed over directly. Similar behavior is implemented for
        ``steem.ws`` which can deal with calls to the **witness
        node**.

        This allows the use of rpc commands similar to the
        ``SteemNodeRPC`` class:

        .. code-block:: python

            steem = SteemExchange(Config)
            # Calls to the cli-wallet
            print(steem.rpc.info())
            # Calls to the witness node
            print(steem.ws.get_account("init0"))
            print(steem.ws.get_asset("USD"))
            print(steem.ws.get_account_count())

    """

    #: Wallet connection parameters
    wallet_host           = "localhost"
    wallet_port           = 8092
    wallet_user           = ""
    wallet_password       = ""

    #: Witness connection parameter
    witness_url           = "ws://localhost:8090/"
    witness_user          = ""
    witness_password      = ""

    #: The account used here
    account               = None
    wif                   = None


class SteemExchange(SteemClient) :
    """ This class serves as an abstraction layer for the decentralized
        exchange within the network and simplifies interaction for
        trading bots.

        :param config config: Configuration Class, similar to the
                              example above

        This class tries to map the poloniex API around the DEX but has
        some differences:

            * market pairs are denoted as 'quote'_'base', e.g. `USD_BTS`
            * Prices/Rates are denoted in 'base', i.e. the USD_BTS market
              is priced in BTS per USD.
              Example: in the USD_BTS market, a price of 300 means
              a USD is worth 300 BTS
            * All markets could be considered reversed as well ('BTS_USD')

        Usage:

        .. code-block:: python

            from steemexchange import SteemExchange
            from pprint import pprint

            class Config():
                wallet_host           = "localhost"
                wallet_port           = 8092
                #witness_url           = "ws://localhost:8090/"
                witness_url           = "wss://steemit.com/wstmp2"
                account = "xeroc"

            steem = SteemExchange(Config)
            pprint(steem.buy(10, "SBD", 100))
            pprint(steem.sell(10, "SBD", 100))
            pprint(steem.returnTicker())
            pprint(steem.return24Volume())
            pprint(steem.returnOrderBook(2))
            pprint(steem.ws.get_order_book(10, api="market_history"))
            pprint(steem.returnTradeHistory())
            pprint(steem.returnMarketHistoryBuckets())
            pprint(steem.returnMarketHistory(300))
            pprint(steem.get_lowest_ask())
            pprint(steem.get_higest_bid())
    """
    #: The trading account
    myAccount = None

    # Available Assets
    assets = ["STEEM", "SBD"]

    def __init__(self, config, **kwargs) :
        # Defaults:
        self.prefix = "STM"

        #: Safe mode
        if "safe_mode" in kwargs:
            self.safe_mode = kwargs["safe_mode"]
        elif hasattr(config, "safe_mode"):
            self.safe_mode = config.safe_mode
        else:
            self.safe_mode = True

        #: The wif key can be used for creating transactions **if** not
        # connected to a cli_wallet
        if not hasattr(config, "wif"):
            setattr(config, "wif", None)
        if not getattr(config, "wif"):
            config.wif = None
        else:
            # Test for valid Private Key
            try:
                config.wif = str(PrivateKey(config.wif))
            except:
                raise InvalidWifKey

        self.config = config
        super().__init__(
            config,
            apis=["database", "network_broadcast", "market_history"]
        )

        # Get my Account
        self.myAccount = self.getMyAccount()

        if not self.myAccount:
            raise ValueError(
                "Couldn't find account name %s" % self.config.account +
                " on the chain! Please double-check!"
            )

        # Now verify that the given wif key has active permissions:
        if getattr(config, "wif") and config.wif:
            pubkey = format(PrivateKey(config.wif).pubkey, self.prefix)
            if not any(filter(
                lambda x: x[0] == pubkey, self.myAccount["active"]["key_auths"]
            )):
                raise WifNotActive

    def executeOps(self, ops):
        expiration = transactions.formatTimeFromNow(30)
        ref_block_num, ref_block_prefix = transactions.getBlockParams(self.ws)
        transaction = transactions.Signed_Transaction(
            ref_block_num=ref_block_num,
            ref_block_prefix=ref_block_prefix,
            expiration=expiration,
            operations=ops
        )
        if self.config.wif:
            transaction = transaction.sign([self.config.wif])
        transaction = transactions.JsonObj(transaction)
        if not (self.safe_mode):
            self.ws.broadcast_transaction(transaction, api="network_broadcast")
        return transaction

    def getMyAccount(self):
        """ Returns the structure containing all data relevant to the
            account specified in the configuration
        """
        if self.config.account:
            return self.ws.get_account(self.config.account)
        else:
            return None

    def formatTimeFromNow(self, secs=0):
        """ Properly Format Time that is `x` seconds in the future

            :param int secs: Seconds to go in the future (`x>0`) or the
                             past (`x<0`)
            :return: Properly formated time for Graphene (`%Y-%m-%dT%H:%M:%S`)
            :rtype: str

        """
        return datetime.utcfromtimestamp(time.time() + int(secs)).strftime('%Y-%m-%dT%H:%M:%S')

    def _get_asset(self, symbol):
        """ Return the properties of the assets tradeable on the
            network.

            :param str symbol: Symbol to get the data for (i.e. STEEM, SBD, VESTS)
        """
        if symbol == "STEEM":
            return {"symbol": "STEEM",
                    "precision": 3
                    }
        elif symbol == "SBD":
            return {"symbol": "SBD",
                    "precision": 3
                    }
        elif symbol == "VESTS":
            return {"symbol": "VESTS",
                    "precision": 6
                    }
        else:
            return None

    def _get_assets(self, quote):
        """ Given the `quote` asset, return base. If quote is SBD, then
            base is STEEM and vice versa.
        """
        assets = self.assets.copy()
        assets.remove(quote)
        base = assets[0]
        return self._get_asset(quote), self._get_asset(base)

    def returnTicker(self):
        """ Returns the ticker for all markets.

            Output Parameters:

            * ``latest``: Price of the order last filled
            * ``lowest_ask``: Price of the lowest ask
            * ``highest_bid``: Price of the highest bid
            * ``sbd_volume``: Volume of SBD
            * ``steem_volume``: Volume of STEEM
            * ``percent_change``: 24h change percentage (in %)

            .. note::

                All prices returned by ``returnTicker`` are in the **reveresed**
                orientation as the market. I.e. in the SBD:STEEM market, prices are
                STEEM per SBD. That way you can multiply prices with `1.05` to
                get a +5%.

            Sample Output:

            .. code-block:: js

                {'SBD:STEEM': {'highest_bid': 3.3222341219615097,
                               'latest': 1000000.0,
                               'lowest_ask': 3.0772668228742615,
                               'percent_change': -0.0,
                               'sbd_volume': 108329611.0,
                               'steem_volume': 355094043.0},
                 'STEEM:SBD': {'highest_bid': 0.30100226633322913,
                               'latest': 0.0,
                               'lowest_ask': 0.3249636958897082,
                               'percent_change': 0.0,
                               'sbd_volume': 108329611.0,
                               'steem_volume': 355094043.0}}


        """
        ticker = {}
        t = self.ws.get_ticker(api="market_history")
        ticker["STEEM:SBD"] = {'highest_bid': float(t['highest_bid']),
                               'latest': float(t["latest"]),
                               'lowest_ask': float(t["lowest_ask"]),
                               'percent_change': float(t["percent_change"]),
                               'sbd_volume': t["sbd_volume"],
                               'steem_volume': t["steem_volume"]}
        ticker["SBD:STEEM"] = {'highest_bid': 1.0 / float(t['highest_bid']),
                               'latest': 1.0 / (float(t["latest"]) or 1e-6),
                               'lowest_ask': 1.0 / float(t["lowest_ask"]),
                               'percent_change': -float(t["percent_change"]),
                               'sbd_volume': t["sbd_volume"],
                               'steem_volume': t["steem_volume"]}
        return ticker

    def return24Volume(self):
        """ Returns the 24-hour volume for all markets, plus totals for primary currencies.

            Sample output:

            .. code-block:: js

                {'sbd_volume': 108329.611, 'steem_volume': 355094.043}

        """
        v = self.ws.get_volume(api="market_history")
        return {'sbd_volume': v["sbd_volume"],
                'steem_volume': v["steem_volume"]}

    def returnOrderBook(self, limit=25):
        """ Returns the order book for the SBD/STEEM markets in both orientations.

            :param int limit: Limit the amount of orders (default: 25)

            Market is SBD:STEEM and prices are STEEM:MARKET

            Sample output:

            .. code-block:: js

                {'asks': [{'price': 3.086436224481787,
                           'sbd': 318547,
                           'steem': 983175},
                          {'price': 3.086429621198315,
                           'sbd': 2814903,
                           'steem': 8688000}],
                 'bids': [{'price': 3.0864376216446257,
                           'sbd': 545133,
                           'steem': 1682519},
                          {'price': 3.086440512632327,
                           'sbd': 333902,
                           'steem': 1030568}]},
        """
        orders = self.ws.get_order_book(limit, api="market_history")
        r = {"asks":[], "bids":[]}
        for side in ["bids", "asks"]:
            for o in orders[side]:
                r[side].append({
                    'price': float(o["price"]),
                    'sbd': o["sbd"] / 10 ** 3,
                    'steem': o["steem"] / 10 ** 3,
                })
        return r

    def returnBalances(self):
        """ Return SBD and STEEM balance of the account
        """
        # riverhead - July 19. 2016
        balances = {}
        result = self.ws.get_account(self.config.account)
        balances["STEEM"] = result['balance']
        balances["SBD"]   = result['sbd_balance']
        return balances

    def returnOpenOrders(self):
        """ Return open Orders of the account
        """
        # riverhead - July 18. 201 6
        orders = self.ws.get_open_orders(self.config.account, limit=1000)
        return orders

    def returnTradeHistory(self, time=1 * 60 * 60, limit=100):
        """ Returns the trade history for the internal market

            :param int hours: Show the last x seconds of trades (default 1h)
            :param int limit: amount of trades to show (<100) (default: 100)
        """
        assert limit <= 100, "'limit' has to be smaller than 100"
        return self.ws.get_trade_history(
            self.formatTimeFromNow(-time),
            self.formatTimeFromNow(),
            limit,
            api="market_history"
        )

    def returnMarketHistoryBuckets(self):
        return self.ws.get_market_history_buckets(api="market_history")

    def returnMarketHistory(
        self,
        bucket_seconds=60 * 5,
        start_age=1 * 60 * 60,
        stop_age=0,
    ):
        """ Return the market history (filled orders).

            :param int bucket_seconds: Bucket size in seconds (see `returnMarketHistoryBuckets()`)
            :param int start_age: Age (in seconds) of the start of the window (default: 1h/3600)
            :param int end_age: Age (in seconds) of the end of the window (default: now/0)

            Example:

            .. code-block:: js

                 {'close_sbd': 2493387,
                  'close_steem': 7743431,
                  'high_sbd': 1943872,
                  'high_steem': 5999610,
                  'id': '7.1.5252',
                  'low_sbd': 534928,
                  'low_steem': 1661266,
                  'open': '2016-07-08T11:25:00',
                  'open_sbd': 534928,
                  'open_steem': 1661266,
                  'sbd_volume': 9714435,
                  'seconds': 300,
                  'steem_volume': 30088443},
        """
        return self.ws.get_market_history(
            bucket_seconds,
            self.formatTimeFromNow(-start_age - stop_age),
            self.formatTimeFromNow(-stop_age),
            api="market_history"
        )

    def buy(self,
            amount,
            quote_symbol,
            rate,
            expiration=7 * 24 * 60 * 60,
            killfill=False):
        """ Places a buy order in a given market (buy ``quote``, sell
            ``base`` in market ``quote_base``). If successful, the
            method will return the order creating (signed) transaction.

            :param number amount: Amount of ``quote`` to buy
            :param str quote_symbol: STEEM, or SBD
            :param float price: price denoted in ``base``/``quote``
            :param number expiration: (optional) expiration time of the order in seconds (defaults to 7 days)
            :param bool killfill: flag that indicates if the order shall be killed if it is not filled (defaults to False)

            Prices/Rates are denoted in 'base', i.e. the STEEM:SBD market
            is priced in SBD per STEEM.

            **Example:** in the SBD:STEEM market, a price of 300 means
            a SBD is worth 300 STEEM
        """
        if self.safe_mode :
            log.warn("Safe Mode enabled! Not broadcasting anything!")
        # We buy quote and pay with base
        quote, base = self._get_assets(quote=quote_symbol)
        if self.rpc:
            transaction = self.rpc.create_order(
                self.config.account,
                random.getrandbits(32),
                '{:.{prec}f} {asset}'.format(
                    amount * rate,
                    prec=base["precision"],
                    asset=base["symbol"]),
                '{:.{prec}f} {asset}'.format(
                    amount,
                    prec=quote["precision"],
                    asset=quote["symbol"]),
                killfill,
                expiration,
                not (self.safe_mode))
        else:
            s = {"owner": self.myAccount["name"],
                 "orderid": random.getrandbits(32),
                 "amount_to_sell": '{:.{prec}f} {asset}'.format(
                     amount * rate,
                     prec=base["precision"],
                     asset=base["symbol"]),
                 "min_to_receive": '{:.{prec}f} {asset}'.format(
                     amount,
                     prec=quote["precision"],
                     asset=quote["symbol"]),
                 "fill_or_kill": killfill,
                 "expiration": transactions.formatTimeFromNow(expiration)
                 }
            order = transactions.Limit_order_create(**s)
            ops = [transactions.Operation(order)]
            transaction = self.executeOps(ops)

        return transaction

    def sell(self,
             amount,
             quote_symbol,
             rate,
             expiration=7 * 24 * 60 * 60,
             killfill=False):
        """ Places a sell order in a given market (sell ``quote``, buy
            ``base`` in market ``quote_base``). If successful, the
            method will return the order creating (signed) transaction.

            :param number amount: Amount of ``quote`` to sell
            :param str quote_symbol: STEEM, or SBD
            :param float price: price denoted in ``base``/``quote``
            :param number expiration: (optional) expiration time of the order in seconds (defaults to 7 days)
            :param bool killfill: flag that indicates if the order shall be killed if it is not filled (defaults to False)

            Prices/Rates are denoted in 'base', i.e. the STEEM:SBD market
            is priced in SBD per STEEM.

            **Example:** in the SBD:STEEM market, a price of 300 means
            a SBD is worth 300 STEEM
        """
        if self.safe_mode :
            log.warn("Safe Mode enabled! Not broadcasting anything!")
        # We buy quote and pay with base
        quote, base = self._get_assets(quote=quote_symbol)
        if self.rpc:
            transaction = self.rpc.create_order(
                self.config.account,
                random.getrandbits(32),
                '{:.{prec}f} {asset}'.format(
                    amount,
                    prec=quote["precision"],
                    asset=quote["symbol"]),
                '{:.{prec}f} {asset}'.format(
                    amount * rate,
                    prec=base["precision"],
                    asset=base["symbol"]),
                killfill,
                expiration,
                not (self.safe_mode))
        else:
            s = {"owner": self.myAccount["name"],
                 "orderid": random.getrandbits(32),
                 "amount_to_sell": '{:.{prec}f} {asset}'.format(
                     amount,
                     prec=quote["precision"],
                     asset=quote["symbol"]),
                 "min_to_receive": '{:.{prec}f} {asset}'.format(
                     amount * rate,
                     prec=base["precision"],
                     asset=base["symbol"]),
                 "fill_or_kill": killfill,
                 "expiration": transactions.formatTimeFromNow(expiration)
                 }
            order = transactions.Limit_order_create(**s)
            ops = [transactions.Operation(order)]
            transaction = self.executeOps(ops)

        return transaction

    def cancel(self, orderNumber):
        """ Cancels an order you have placed in a given market. Requires
            only the "orderNumber". An order number takes the form
            ``1.7.xxx``.

            :param str orderNumber: The Order Object ide of the form ``1.7.xxxx``
        """
        if self.safe_mode :
            log.warn("Safe Mode enabled! Not broadcasting anything!")
        if self.rpc:
            transaction = self.rpc.cancel_order(
                self.config.account,
                orderNumber,
                not self.safe_mode)
        else:
            s = {"owner": self.myAccount["name"],
                 "orderid": orderNumber,
                 }
            order = transactions.Limit_order_cancel(**s)
            ops = [transactions.Operation(order)]
            transaction = self.executeOps(ops)

        return transaction

    def get_lowest_ask(self):
        """ Return the lowest ask.

            Example:

            .. code-block:: js

                {'SBD:STEEM': [{'price': 3.08643564387293, 'sbd': 320863, 'steem': 990323}],
                 'STEEM:SBD': [{'price': '0.32399833185738391',
                                'sbd': 320863,
                                'steem': 990323}]}
        """
        r = {}
        orders = self.returnOrderBook(1)
        for m in orders:
            r[m] = orders[m]["asks"]
        return r

    def get_higest_bid(self):
        """ Return the highest bid.

            Example:

            .. code-block:: js

                {'SBD:STEEM': [{'price': 3.08643564387293, 'sbd': 320863, 'steem': 990323}],
                 'STEEM:SBD': [{'price': '0.32399833185738391',
                                'sbd': 320863,
                                'steem': 990323}]}
        """
        r = {}
        orders = self.returnOrderBook(1)
        for m in orders:
            r[m] = orders[m]["bids"]
        return r

    def transfer(self, amount, asset, recepient, memo=""):
        """ Transfer SBD or STEEM to another account

            :param float amount: Amount to transfer
            :param str asset: Asset to transfer ("SBD" or "STEEM")
            :param str recepient: Recepient of the transfer
            :param str memo: (Optional) Memo attached to the transfer
        """
        if self.safe_mode :
            log.warn("Safe Mode enabled! Not broadcasting anything!")
        asset = self._get_asset(asset)
        if self.rpc:
            print((
                self.config.account,
                recepient,
                '{:.{prec}f} {asset}'.format(
                    amount,
                    prec=asset["precision"],
                    asset=asset["symbol"]
                ),
                memo,
                not (self.safe_mode)))
            transaction = self.rpc.transfer(
                self.config.account,
                recepient,
                '{:.{prec}f} {asset}'.format(
                    amount,
                    prec=asset["precision"],
                    asset=asset["symbol"]
                ),
                memo,
                not (self.safe_mode))
        else:
            op = transactions.Transfer(
                **{"from": self.config.account,
                   "to": recepient,
                   "amount": '{:.{prec}f} {asset}'.format(
                       amount,
                       prec=asset["precision"],
                       asset=asset["symbol"]
                   ),
                   "memo": memo
                   }
            )
            ops = [transactions.Operation(op)]
            transaction = self.executeOps(ops)

        return transaction
