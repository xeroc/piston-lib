Welcome to python-steem's documentation!
===============================================

Library
-------

Piston can be used as a library and thus helps you

* deal with configuration settings (node, prefered options, ..)
* accounts and private keys (with integrated wallet)
* presentation of Steem content

It further can be used to easily deploy bots on steem. The most easy
auto-reply bot can be coded with just a few lines of code:

.. code-block:: python

   from steem import Steem
   import os
   import json
   steem = Steem(wif="<posting-key-for-default-author>")
   for c in steem.stream_comments():
       if "Boobie" in c["body"]:
           print(c.reply(".. doobidoo"))

Python-Steem Libraries
-------------------------

.. toctree::
   :maxdepth: 3

   installation
   steem
   stream
   exchange

Low Level Classes
-----------------

.. toctree::
   :maxdepth: 3

   rpc
   websocketrpc
   asyncclient
   transactions
   client
