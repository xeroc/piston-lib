********
Exchange
********

Quickstart
==========

.. code-block:: python

    from pprint import pprint
    from steemexchange import SteemExchange

    class Config():
        witness_url     = "wss://this.piston.rocks/"
        account         = "xeroc"
        # Either provide a cli-wallet RPC
        wallet_host     = "localhost"
        wallet_port     = 8092
        # or the (active) private key for your account
        wif             = ""

    steem = SteemExchange(Config)
    pprint(steem.buy(10, "SBD", 100))
    pprint(steem.sell(10, "SBD", 100))
    pprint(steem.cancel("24432422"))
    pprint(steem.returnTicker())
    pprint(steem.return24Volume())
    pprint(steem.returnOrderBook(2))
    pprint(steem.ws.get_order_book(10, api="market_history"))
    pprint(steem.returnTradeHistory())
    pprint(steem.returnMarketHistoryBuckets())
    pprint(steem.returnMarketHistory(300))
    pprint(steem.get_lowest_ask())
    pprint(steem.get_higest_bid())
    pprint(steem.transfer(10, "SBD", "fabian", "foobar"))

Definition
===========

.. autoclass:: steemexchange.exchange.SteemExchange
    :members:
