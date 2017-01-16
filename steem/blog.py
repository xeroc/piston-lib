import steem as stm
from funcy import rest, first
from steem.account import Account
from steem.post import Post
from steem.utils import is_comment


class Blog(list):
    def __init__(self, account_name, steem_instance=None):
        if not steem_instance:
            steem_instance = stm.Steem()
        self.steem = steem_instance
        self.name = account_name
        self.refresh()

    def refresh(self):
        state = self.steem.rpc.get_state("/@%s/blog" % self.name)
        posts = state["accounts"].get(self.name, {}).get("blog", [])
        r = []
        for p in posts:
            post = state["content"][p]
            r.append(Post(post, steem_instance=self))
        super(Blog, self).__init__(r)

    def all(self):
        self.current_index = Account(self.name).virtual_op_count()

        # prevent duplicates
        self.seen_items = set()

        while True:
            # fetch the next batch
            if self.current_index == 0:
                raise StopIteration

            limit = 1000
            if self.current_index < 1000:
                # avoid duplicates on last batch
                limit = 1000 - self.current_index
                self.current_index = 1000

            h = self.steem.rpc.get_account_history(self.name, self.current_index, limit)
            if not h:
                raise StopIteration

            self.current_index -= 1000

            # filter out irrelevant items
            def blogpost_only(item):
                op_type, op = item[1]['op']
                return op_type == 'comment' and not is_comment(op)

            hist = filter(blogpost_only, h)
            hist = map(lambda x: x[1]['op'][1], hist)
            hist = [x for x in hist if x['author'] == self.name]

            # filter out items that have been already passed on
            # this is necessary because post edits create multiple entries in the chain
            hist_uniq = []
            for item in hist:
                if item['permlink'] not in self.seen_items:
                    self.seen_items.add(item['permlink'])
                    hist_uniq.append(item)

            for p in hist_uniq:
                yield Post(p)
