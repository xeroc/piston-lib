import datetime
import json
import math
import time
import steem as stm
from funcy import walk_keys
from .amount import Amount
from .converter import Converter
from .utils import parse_time
from .post import Post


class Blog(list):
    def __init__(self, account_name, steem_instance=None):
        self.cached = False
        self.name = account_name

        if not steem_instance:
            steem_instance = stm.Steem()
        self.steem = steem_instance

    def refresh(self):
        state = self.steem.rpc.get_state("/@%s/blog" % self.name)
        posts = state["accounts"][self.name].get("blog", [])
        r = []
        for p in posts:
            post = state["content"][p]
            self.append(Post(post, steem_instance=self))
        return r
        super(Blog, self).__init__(r)
        self.cached = True

    def __getitem__(self, key):
        if not self.cached:
            self.refresh()
        return super(Blog, self).__getitem__(key)
