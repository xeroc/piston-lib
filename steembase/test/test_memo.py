from steembase import transactions
from graphenebase.account import PrivateKey, PublicKey, Address
from steembase import memo as Memo
import random
import unittest


class Testcases(unittest.TestCase) :

    def __init__(self, *args, **kwargs):
        super(Testcases, self).__init__(*args, **kwargs)
        self.maxDiff = None

    def test_memo(self):

        from_priv = "5KNK3bejeP3PtQ1Q9EagBmGacYFCZ3qigRAZDbfqcdjDWWmZSMm"
        to_priv = "5K2JRPe1iRwD2He5DyDRtHs3Z1wpom3YXguFxEd57kNTHhQuZ2k"

        for msg in [
            "foobar",
            "just a donation",
            "1124safafASFasc",
        ]:
            nonce = str(random.getrandbits(64))
            memo = Memo.encode_memo(
                PrivateKey(from_priv),
                PrivateKey(to_priv).pubkey,
                nonce,
                msg
            )
            plain = Memo.decode_memo(
                PrivateKey(to_priv),
                memo
            )
            self.assertEqual(msg, plain)
