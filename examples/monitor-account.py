from steemapi.steemnoderpc import SteemNodeRPC
from pprint import pprint
import time

"""
   Connection Parameters to steemd daemon.

   Start the steemd daemon with the rpc-endpoint parameter:

      ./programs/steemd/steemd --rpc-endpoint=127.0.0.1:8092

    This opens up a RPC port (e.g. at 8092). Currently, authentication
    is not yet available, thus, we recommend to restrict access to
    localhost. Later we will allow authentication via username and
    passpword (both empty now).

"""
rpc = SteemNodeRPC("ws://localhost:8090", "", "")

"""
    Last Block that you have process in your backend.
    Processing will continue at `last_block + 1`
"""
last_block = 160900

"""
    Deposit account name to monitor
"""
watch_account = "world"


def process_block(block, blockid):
    """
        This call processes a block which can carry many transactions

        :param Object block: block data
        :param number blockid: block number
    """
    if "transactions" in block:
        for tx in block["transactions"]:
            #: Parse operations
            for opObj in tx["operations"]:
                #: Each operation is an array of the form
                #:    [type, {data}]
                opType = opObj[0]
                op = opObj[1]

                # we here want to only parse transfers
                if opType == "transfer":
                    process_transfer(op, block, blockid)


def process_transfer(op, block, blockid):
    """
        We here process the actual transfer operation.
    """
    if op["to"] == watch_account:
        print(
            "%d | %s | %s -> %s: %s -- %s" % (
                blockid,
                block["timestamp"],
                op["from"],
                op["to"],
                op["amount"],
                op["memo"]
            )
        )


if __name__ == '__main__':
    # Let's find out how often blocks are generated!
    config = rpc.get_config()
    block_interval = config["STEEMIT_BLOCK_INTERVAL"]

    # We are going to loop indefinitely
    while True:

        # Get chain properies to identify the
        # head/last reversible block
        props = rpc.get_dynamic_global_properties()

        # Get block number
        # We here have the choice between
        #  * head_block_number: the last block
        #  * last_irreversible_block_num: the block that is confirmed by
        #    2/3 of all block producers and is thus irreversible!
        # We recommend to use the latter!
        # block_number = props['head_block_number']
        block_number = props['last_irreversible_block_num']

        # We loop through all blocks we may have missed since the last
        # block defined above
        while (block_number - last_block) > 0:
            last_block += 1

            # Get full block
            block = rpc.get_block(last_block)

            # Process block
            process_block(block, last_block)

        # Sleep for one block
        time.sleep(block_interval)
