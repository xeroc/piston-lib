import steem as stm
from funcy import rest, first
from steem.account import Account
from steem.post import Post
from steem.utils import is_comment


class Blog:
    def __init__(self, account_name, steem_instance=None):
        if not steem_instance:
            steem_instance = stm.Steem()
        self.steem = steem_instance

        self.account = Account(account_name)
        self.current_index = self.account.virtual_op_count()
        self.history = None

        # prevent duplicates
        self.seen_items = set()

    def refresh(self):
        # fetch the next batch
        if self.current_index == 0:
            raise StopIteration

        limit = 1000
        if self.current_index < 1000:
            # avoid duplicates on last batch
            limit = 1000 - self.current_index
            self.current_index = 1000

        h = self.steem.rpc.get_account_history(self.account.name, self.current_index, limit)
        if not h:
            raise StopIteration

        self.current_index -= 1000

        # filter out irrelevant items
        def blogpost_only(item):
            op_type, op = item[1]['op']
            return op_type == 'comment' and not is_comment(op)

        hist = filter(blogpost_only, h)
        hist = map(lambda x: x[1]['op'][1], hist)
        hist = [x for x in hist if x['author'] == self.account.name]

        # filter out items that have been already passed on
        # this is necessary because post edits create multiple entries in the chain
        hist_uniq = []
        for item in hist:
            if item['permlink'] not in self.seen_items:
                self.seen_items.add(item['permlink'])
                hist_uniq.append(item)

        # LIFO
        self.history = hist_uniq[::-1]

    def __iter__(self):
        return self

    def __next__(self):
        while not self.history:
            self.refresh()

        # consume an item from history
        next_item = first(self.history)
        self.history = list(rest(self.history))

        return Post(next_item)
