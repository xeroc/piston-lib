********
Exchange
********

Quickstart
==========

.. code-block:: python

    from pprint import pprint
    from steem import Steem
    from steem.dex import Dex

    steem = Steem()
    dex = Dex(steem)
    pprint(dex.buy(10, "SBD", 100))
    pprint(dex.sell(10, "SBD", 100))
    pprint(dex.cancel("24432422"))
    pprint(dex.returnTicker())
    pprint(dex.return24Volume())
    pprint(dex.returnOrderBook(2))
    pprint(dex.ws.get_order_book(10, api="market_history"))
    pprint(dex.returnTradeHistory())
    pprint(dex.returnMarketHistoryBuckets())
    pprint(dex.returnMarketHistory(300))
    pprint(dex.get_lowest_ask())
    pprint(dex.get_higest_bid())
    pprint(dex.transfer(10, "SBD", "fabian", "foobar"))

Definition
===========

.. autoclass:: steem.dex.Dex
    :members:
