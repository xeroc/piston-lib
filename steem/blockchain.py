import steem as stm
from steem.utils import parse_time


class Blockchain(object):
    def __init__(self, steem_instance=None):
        """ This class allows to access the blockchain and read data
            from it

            :param Steem steem: Steem() instance to use when accesing a RPC
        """
        if not steem_instance:
            steem_instance = stm.Steem()
        self.steem = steem_instance

    def info(self):
        """ This call returns the *dynamic global properties*
        """
        return self.steem.rpc.get_dynamic_global_properties()

    def get_current_block(self, mode='last_irreversible_block_num'):
        """ This call returns the current block

            :param str mode: (default)Irreversible block
                    (``last_irreversible_block_num``) or actual head block
                    (``head_block_number``)
        """
        assert mode == 'last_irreversible_block_num' or mode == "head_block_number"
        return self.info().get(mode)

    def stream(self, **kwargs):
        """ Yield specific operations (e.g. comments) only

            :param array opNames: List of operations to filter for, e.g.
                vote, comment, transfer, transfer_to_vesting,
                withdraw_vesting, limit_order_create, limit_order_cancel,
                feed_publish, convert, account_create, account_update,
                witness_update, account_witness_vote, account_witness_proxy,
                pow, custom, report_over_production, fill_convert_request,
                comment_reward, curate_reward, liquidity_reward, interest,
                fill_vesting_withdraw, fill_order,
            :param int start: Start at this block
            :param int stop: Stop at this block
            :param str mode: We here have the choice between
                 * "head": the last block
                 * "irreversible": the block that is confirmed by 2/3 of all block producers and is thus irreversible!
        """
        return self.steem.rpc.stream(**kwargs)

    def replay(self, start_block=1, end_block=None, filter_by=list(), **kwargs):
        """ Same as ``stream`` with different prototyp
        """
        return self.steem.rpc.stream(
            opNames=filter_by,
            start=start_block,
            stop=end_block,
            **kwargs
        )

    def block_time(self, block_num):
        """ Returns a datetime of the block with the given block
            number.

            :param int block_num: Block number
        """
        block = self.steem.rpc.get_block(block_num)
        return parse_time(block['timestamp']).timestamp()

    def block_timestamp(self, block_num):
        """ Returns the timestamp of the block with the given block
            number.

            :param int block_num: Block number
        """
        block = self.steem.rpc.get_block(block_num)
        return int(parse_time(block['timestamp']).timestamp())

    def get_block_from_time(self, timestring, error_margin=10, mode="last_irreversible_block_num"):
        """ Estimate block number from given time

            :param str timestring: String representing time
            :param int error_margin: Estimate block number within this interval (in seconds)
            :param str mode: (default)Irreversible block
                    (``last_irreversible_block_num``) or actual head block
                    (``head_block_number``)

        """
        known_block = self.get_current_block(mode)
        known_block_timestamp = self.block_timestamp(known_block)
        timestring_timestamp = parse_time(timestring).timestamp()
        delta = known_block_timestamp - timestring_timestamp
        block_delta = delta / 3
        guess_block = known_block - block_delta
        guess_block_timestamp = self.block_timestamp(guess_block)
        error = timestring_timestamp - guess_block_timestamp
        while abs(error) > error_margin:
            guess_block += error / 3
            guess_block_timestamp = self.block_timestamp(guess_block)
            error = timestring_timestamp - guess_block_timestamp
        return int(guess_block)

    def get_all_accounts(self, start='', stop='', steps=1e6):
        """ Yields account names between start and stop.

            :param str start: Start at this account name
            :param str stop: Stop at this account name
            :param int steps: Obtain ``steps`` names with a single call from RPC
        """
        lastname = start
        while True:
            names = self.steem.rpc.lookup_accounts(lastname, steps)
            for name in names:
                yield name
                if name == stop:
                    break
            if lastname == names[-1]:
                break
            lastname = names[-1]
            if len(names) < steps:
                break
