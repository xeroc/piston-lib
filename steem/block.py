from . import steem as stm
from .exceptions import BlockDoesNotExistsException
from .utils import parse_time


class Block(dict):
    def __init__(
        self,
        block,
        steem_instance=None,
        lazy=False
    ):
        self.cached = False
        self.block = block

        if not steem_instance:
            steem_instance = stm.Steem()
        self.steem = steem_instance

        if isinstance(block, Block):
            super(Block, self).__init__(block)
            self.cached = True
        elif not lazy:
            self.refresh()

    def refresh(self):
        block = self.steem.rpc.get_block(self.block)
        if not block:
            raise BlockDoesNotExistsException
        super(Block, self).__init__(block)
        self.cached = True

    def __getitem__(self, key):
        if not self.cached:
            self.refresh()
        return super(Block, self).__getitem__(key)

    def items(self):
        if not self.cached:
            self.refresh()
        return super(Block, self).items()

    def time(self):
        return parse_time(self['timestamp'])
