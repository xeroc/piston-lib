from .block import Block
from . import steem as stm
from .utils import parse_time


class Blockchain(object):
    def __init__(
        self,
        steem_instance=None,
        mode="irreversible"
    ):
        """ This class allows to access the blockchain and read data
            from it

            :param Steem steem: Steem() instance to use when accesing a RPC
            :param str mode: (default) Irreversible block
                    (``irreversible``) or actual head block (``head``)
        """
        if not steem_instance:
            steem_instance = stm.Steem()
        self.steem = steem_instance

        if mode == "irreversible":
            self.mode = 'last_irreversible_block_num'
        elif mode == "head":
            self.mode = "head_block_number"
        else:
            raise ValueError("invalid value for 'mode'!")

    def info(self):
        """ This call returns the *dynamic global properties*
        """
        return self.steem.rpc.get_dynamic_global_properties()

    def get_current_block_num(self):
        """ This call returns the current block
        """
        return self.info().get(self.mode)

    def get_current_block(self):
        """ This call returns the current block
        """
        return Block(self.get_current_block_num())

    def blocks(self, **kwargs):
        """ Yield Blocks as a generator

            :param int start: Start at this block
            :param int stop: Stop at this block
        """
        return self.steem.rpc.block_stream(**kwargs)

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
        """
        return self.steem.rpc.stream(**kwargs)

    def replay(self, start_block=1, end_block=None, filter_by=list(), **kwargs):
        """ Same as ``stream`` with different prototyp
        """
        return self.steem.rpc.stream(
            opNames=filter_by,
            start=start_block,
            stop=end_block,
            mode=self.mode,
            **kwargs
        )

    def block_time(self, block_num):
        """ Returns a datetime of the block with the given block
            number.

            :param int block_num: Block number
        """
        return Block(block_num).time()

    def block_timestamp(self, block_num):
        """ Returns the timestamp of the block with the given block
            number.

            :param int block_num: Block number
        """
        return int(Block(block_num).time().timestamp())

    def get_block_from_time(self, timestring, error_margin=10):
        """ Estimate block number from given time

            :param str timestring: String representing time
            :param int error_margin: Estimate block number within this interval (in seconds)

        """
        known_block = self.get_current_block()
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
