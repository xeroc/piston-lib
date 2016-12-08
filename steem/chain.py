import time

import dateutil
from dateutil import parser

from steem import Steem


class Blockchain(object):
    def __init__(self, steem_instance=None):
        if not steem_instance:
            steem_instance = Steem()
        self.steem = steem_instance

    @staticmethod
    def parse_block(block, block_id, verbose=False, **kwargs):
        if "transactions" in block:
            timestamp = block['timestamp']
            if verbose:
                print("Processing #%d - %s" % (block_id, timestamp))
            for tx in block["transactions"]:
                for opObj in tx["operations"]:
                    op_type = opObj[0]
                    op = opObj[1]

                    yield {
                        "block_id": block_id,
                        "timestamp": timestamp,
                        "op_type": op_type,
                        "op": op,
                    }

    def stream(self, **kwargs):
        return self.replay(start_block=self.get_current_block(), **kwargs)

    def replay(self, start_block=1, end_block=None, filter_by=None, **kwargs):
        """
        :param start_block: Block number of the first block to parse.
        :param end_block: Block number of the last block to parse.
        :param filter_by: A string or list of filters. ie: "vote" or ["comment", "vote"]
        :param kwargs: Arguments for the parser, namely verbose=False
        :return: Returns a generator
        """
        # Let's find out how often blocks are generated!
        config = self.steem.rpc.get_config()
        block_interval = config["STEEMIT_BLOCK_INTERVAL"]

        # last confirmed vs head
        last_block_mode = 'head_block_number' if 'head' in kwargs else 'last_irreversible_block_num'

        current_block = start_block

        while True:
            props = self.steem.rpc.get_dynamic_global_properties()
            last_confirmed_block = props[last_block_mode]

            while current_block < last_confirmed_block:

                block = self.steem.rpc.get_block(current_block)
                if block is None:
                    raise LookupError('Block is None. Are you trying to fetch a block from the future?')
                for operation in self.parse_block(block, current_block, **kwargs):
                    if filter_by is None:
                        yield operation
                    else:
                        if type(filter_by) is list:
                            if operation['op_type'] in filter_by:
                                yield operation

                        if type(filter_by) is str:
                            if operation['op_type'] == filter_by:
                                yield operation

                current_block += 1

                if end_block is not None and current_block >= end_block:
                    print("All done!")
                    return

            # Sleep for one block
            time.sleep(block_interval)

    def get_current_block(self):
        return self.steem.rpc.get_dynamic_global_properties()['last_irreversible_block_num']

    def get_block_time(self, block_num, verbose=False):
        block = self.steem.rpc.get_block(block_num)
        time = block['timestamp']
        if verbose:
            print("Block %d was minted on: %s" % (block_num, time))
        return dateutil.parser.parse(time + "UTC").timestamp()

    def get_block_from_time(self, timestring, error_margin=10, verbose=False):
        known_block = self.get_current_block()
        known_block_timestamp = self.get_block_time(known_block)

        timestring_timestamp = dateutil.parser.parse(timestring + "UTC").timestamp()

        delta = known_block_timestamp - timestring_timestamp
        block_delta = delta / 3

        if verbose:
            print("Guess:")
        guess_block = known_block - block_delta
        guess_block_timestamp = self.get_block_time(guess_block, verbose=verbose)

        error = timestring_timestamp - guess_block_timestamp
        while abs(error) > error_margin:
            if verbose:
                print("Error: %s" % error)
            guess_block += error / 3
            guess_block_timestamp = self.get_block_time(guess_block, verbose=verbose)

            error = timestring_timestamp - guess_block_timestamp

        return int(guess_block)

    def get_all_usernames(self):
        return self.steem.rpc.lookup_accounts('', 1e6)

