import datetime
import json
import math
import time
from contextlib import suppress

import steem as stm
from funcy import walk_keys

from .amount import Amount
from .converter import Converter
from .exceptions import AccountDoesNotExistsException
from .utils import parse_time


class Account(dict):
    def __init__(
        self,
        account_name,
        steem_instance=None,
        lazy=False,
    ):
        self.cached = False
        self.name = account_name

        if not steem_instance:
            steem_instance = stm.Steem()
        self.steem = steem_instance

        # caches
        self._converter = None

        if not lazy:
            self.refresh()

    def refresh(self):
        account = self.steem.rpc.get_account(self.name)
        if not account:
            raise AccountDoesNotExistsException
        super(Account, self).__init__(account)
        self.cached = True

    def __getitem__(self, key):
        if not self.cached:
            self.refresh()
        return super(Account, self).__getitem__(key)

    def items(self):
        if not self.cached:
            self.refresh()
        return super(Account, self).items()

    @property
    def converter(self):
        if not self._converter:
            self._converter = Converter(self.steem)
        return self._converter

    @property
    def profile(self):
        with suppress(Exception):
            meta_str = self.get("json_metadata", "")
            return json.loads(meta_str).get('profile', dict())

    @property
    def sp(self):
        vests = Amount(self['vesting_shares']).amount
        return self.converter.vests_to_sp(vests)

    @property
    def rep(self):
        return self.reputation()

    def get_balances(self, asfloat=False):
        my_account_balances = self.steem.get_balances(self.name)
        balance = {
            "STEEM": my_account_balances["balance"],
            "SBD": my_account_balances["sbd_balance"],
            "VESTS": my_account_balances["vesting_shares"],
            "SAVINGS_STEEM": my_account_balances["savings_balance"],
            "SAVINGS_SBD": my_account_balances["savings_sbd_balance"]
        }
        if asfloat:
            return {k: v.amount for k, v in balance.items()}
        else:
            return balance

    def reputation(self, precision=2):
        rep = int(self['reputation'])
        if rep < 0:
            return -1
        if rep == 0:
            return 25

        score = (math.log10(abs(rep)) - 9) * 9 + 25
        return round(score, precision)

    def voting_power(self):
        return self['voting_power'] / 100

    def get_followers(self):
        return [x['follower'] for x in self._get_followers(direction="follower")]

    def get_following(self):
        return [x['following'] for x in self._get_followers(direction="following")]

    def _get_followers(self, direction="follower", last_user=""):
        if direction == "follower":
            followers = self.steem.rpc.get_followers(self.name, last_user, "blog", 100, api="follow")
        elif direction == "following":
            followers = self.steem.rpc.get_following(self.name, last_user, "blog", 100, api="follow")
        if len(followers) >= 100:
            followers += self._get_followers(direction=direction, last_user=followers[-1][direction])[1:]
        return followers

    def has_voted(self, post):
        active_votes = {v["voter"]: v for v in getattr(post, "active_votes")}
        return self.name in active_votes

    def curation_stats(self):
        trailing_24hr_t = time.time() - datetime.timedelta(hours=24).total_seconds()
        trailing_7d_t = time.time() - datetime.timedelta(days=7).total_seconds()

        reward_24h = 0.0
        reward_7d = 0.0

        for reward in self.history2(filter_by="curation_reward", take=10000):

            timestamp = parse_time(reward['timestamp']).timestamp()
            if timestamp > trailing_7d_t:
                reward_7d += Amount(reward['reward']).amount

            if timestamp > trailing_24hr_t:
                reward_24h += Amount(reward['reward']).amount

        reward_7d = self.converter.vests_to_sp(reward_7d)
        reward_24h = self.converter.vests_to_sp(reward_24h)
        return {
            "24hr": reward_24h,
            "7d": reward_7d,
            "avg": reward_7d / 7,
        }

    def virtual_op_count(self):
        try:
            last_item = self.steem.rpc.get_account_history(self.name, -1, 0)[0][0]
        except IndexError:
            return 0
        else:
            return last_item

    def history(self, filter_by=None, start=0):
        """
        Take all elements from start to last from history, oldest first.
        """
        batch_size = 1000
        max_index = self.virtual_op_count()
        if not max_index:
            return

        start_index = start + batch_size
        i = start_index
        while True:
            if i == start_index:
                limit = batch_size
            else:
                limit = batch_size - 1
            history = self.steem.rpc.get_account_history(self.name, i, limit)
            for item in history:
                index = item[0]
                if index >= max_index:
                    return

                op_type = item[1]['op'][0]
                op = item[1]['op'][1]
                timestamp = item[1]['timestamp']
                trx_id = item[1]['trx_id']

                def construct_op(account_name):
                    return {
                        **op,
                        "index": index,
                        "account": account_name,
                        "trx_id": trx_id,
                        "timestamp": timestamp,
                        "type": op_type,
                    }

                if filter_by is None:
                    yield construct_op(self.name)
                else:
                    if type(filter_by) is list:
                        if op_type in filter_by:
                            yield construct_op(self.name)

                    if type(filter_by) is str:
                        if op_type == filter_by:
                            yield construct_op(self.name)
            i += batch_size

    def history2(self, filter_by=None, take=1000):
        """
        Take X elements from most recent history, oldest first.
        """
        max_index = self.virtual_op_count()
        start_index = max_index - take
        if start_index < 0:
            start_index = 0

        return self.history(filter_by, start=start_index)

    def get_account_votes(self):
        return self.steem.rpc.get_account_votes(self.name)

    def get_withdraw_routes(self):
        return self.steem.rpc.get_withdraw_routes(self.name, 'all')

    def get_conversion_requests(self):
        return self.steem.rpc.get_conversion_requests(self.name)

    @staticmethod
    def filter_by_date(items, start_time, end_time=None):
        start_time = parse_time(start_time).timestamp()
        if end_time:
            end_time = parse_time(end_time).timestamp()
        else:
            end_time = time.time()

        filtered_items = []
        for item in items:
            if 'time' in item:
                item_time = item['time']
            elif 'timestamp' in item:
                item_time = item['timestamp']
            timestamp = parse_time(item_time).timestamp()
            if end_time > timestamp > start_time:
                filtered_items.append(item)

        return filtered_items

    def export(self):
        """ This method returns a dictionary that is type-safe to store as JSON or in a database.
        """
        self.refresh()
        followers = self.get_followers()
        following = self.get_following()

        return {
            **self,
            "profile": self.profile,
            "sp": self.sp,
            "rep": self.rep,
            "balances": walk_keys(str.upper, self.get_balances()),
            "followers": followers,
            "followers_count": len(followers),
            "following": following,
            "following_count": len(following),
            "curation_stats": self.curation_stats(),
            "withdrawal_routes": self.get_withdraw_routes(),
            "conversion_requests": self.get_conversion_requests(),
            "account_votes": self.get_account_votes(),
        }
