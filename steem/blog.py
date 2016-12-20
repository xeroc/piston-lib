import datetime
import json
import math
import time
import steem as stm
from funcy import walk_keys
from steem.amount import Amount
from steem.converter import Converter
from steem.utils import parse_time


class Blog(list):
    def __init__(self, account_name, steem_instance=None):
        if not steem_instance:
            steem_instance = stm.Steem()
        self.steem = steem_instance

        self.name = account_name
        posts = self.steem.get_blog(self.name)
        super(Blog, self).__init__(posts)
