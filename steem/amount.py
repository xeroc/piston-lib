import math

from werkzeug.contrib.cache import SimpleCache

from steem import Steem
from steem.utils import simple_cache

converter_cache = SimpleCache()


class Amount(object):
    def __init__(self, amountString):
        self.amount, self.asset = amountString.split(" ")
        self.amount = float(self.amount)

    def __str__(self):
        if self.asset == "SBD":
            prec = 3
        elif self.asset == "STEEM":
            prec = 3
        elif self.asset == "VESTS":
            prec = 6
        else:
            prec = 6
        return "{:.{prec}f} {}".format(self.amount, self.asset, prec=prec)


class Converter(object):
    def __init__(self, steem_instance=None):
        if not steem_instance:
            steem_instance = Steem()
        self.steem = steem_instance

        self.CONTENT_CONSTANT = 2000000000000

    @simple_cache(converter_cache, timeout=5 * 60)
    def sbd_median_price(self):
        return Amount(self.steem.rpc.get_feed_history()['current_median_history']['base']).amount

    @simple_cache(converter_cache, timeout=5 * 60)
    def steem_per_mvests(self):
        info = self.steem.rpc.get_dynamic_global_properties()
        return (
            Amount(info["total_vesting_fund_steem"]).amount /
            (Amount(info["total_vesting_shares"]).amount / 1e6)
        )

    def vests_to_sp(self, vests):
        return vests * self.steem_per_mvests() / 1e6

    def sp_to_vests(self, sp):
        return sp * 1e6 / self.steem_per_mvests()

    def sp_to_rshares(self, sp, voting_power=10000, vote_pct=10000):
        # calculate our account voting shares (from vests), mine is 6.08b
        vesting_shares = int(self.sp_to_vests(sp) * 1e6)

        # calculate vote rshares
        power = (((voting_power * vote_pct) / 10000) / 200) + 1
        rshares = (power * vesting_shares) / 10000

        return rshares

    def steem_to_sbd(self, amount_steem):
        return self.sbd_median_price() * amount_steem

    def sbd_to_steem(self, amount_sbd):
        return amount_sbd / self.sbd_median_price()

    def sbd_to_shares(self, sbd_payout):
        steem_payout = self.sbd_to_steem(sbd_payout)

        props = self.steem.rpc.get_dynamic_global_properties()
        total_reward_fund_steem = Amount(props['total_reward_fund_steem']).amount
        total_reward_shares2 = int(props['total_reward_shares2'])

        post_rshares2 = (steem_payout / total_reward_fund_steem) * total_reward_shares2

        rshares = math.sqrt(self.CONTENT_CONSTANT ** 2 + post_rshares2) - self.CONTENT_CONSTANT
        return rshares

    def rshares_2_weight(self, rshares):
        _max = 2 ** 64 - 1
        return (_max * rshares) / (2 * self.CONTENT_CONSTANT + rshares)
