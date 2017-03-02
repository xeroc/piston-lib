Account
~~~~~~~

Obtaining data of an account.

.. code-block:: python

   from piston.account import Account
   account = Account("xeroc")
   print(account)
   print(account.reputation())
   print(account.balances)

.. autoclass:: piston.account.Account
   :members:
