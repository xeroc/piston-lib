Account
~~~~~~~

Obtaining data of an account.

.. code-block:: python

   from steem.account import Account
   account = Account("xeroc")
   print(account)
   print(account.reputation())
   print(account.balances)

.. autoclass:: steem.account.Account
   :members:
