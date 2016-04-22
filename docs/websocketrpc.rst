************
WebsocketRPC
************

.. warning:: This is a low level class that can be used in combination with
             ``SteemClient``. Do not use this class unless you know what
             you are doing!

This class allows to call API methods exposed by the witness node via
websockets. It does **not** support notifications and is not run
asynchronously.

.. autoclass:: steemapi.steemwsrpc.SteemWebsocketRPC
     :members:
