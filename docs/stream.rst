***********
SteemStream
***********

This module allows to stream blocks and individual operations from the
blockchain and run bots with a minimum of code.

Example
=======

This example code shows all comments starting at block 1893850.

.. code-block:: python

   from steemapi.steemnoderpc import SteemNodeRPC
   from pprint import pprint

   rpc = SteemNodeRPC("wss://steemit.com/ws")

   for a in rpc.stream("comment", start=1893850):
       pprint(a)

Definition
===========

.. autoclass:: steemapi.steemnoderpc.SteemNodeRPC
    :members: stream
