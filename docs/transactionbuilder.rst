Transaction Builder
~~~~~~~~~~~~~~~~~~~

To build your own transactions and sign them

.. code-block:: python

   from piston.transactionbuilder import TransactionBuilder
   from pistonbase.operations import Vote
   tx = TransactionBuilder()
   tx.appendOps(Vote(
       **{"voter": voter,
          "author": post_author,
          "permlink": post_permlink,
          "weight": int(weight * STEEMIT_1_PERCENT)}  # STEEMIT_1_PERCENT = 100
   ))
   tx.appendSigner("xeroc", "posting")
   tx.sign()
   tx.broadcast()

.. autoclass:: piston.transactionbuilder.TransactionBuilder
   :members:
