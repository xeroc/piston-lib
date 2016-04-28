from steembase import transactions
from graphenebase.account import PrivateKey, PublicKey, Address
import random
import unittest
from pprint import pprint
from binascii import hexlify


class Testcases(unittest.TestCase) :

    def test_Comment(self):
        wif              = "5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3"
        ref_block_num    = 34294
        ref_block_prefix = 3707022213
        expiration       = "2016-04-06T08:29:27"

        op = transactions.Comment(
            **{"parent_author": "foobara",
               "parent_permlink": "foobarb",
               "author": "foobarc",
               "permlink": "foobard",
               "title": "foobare",
               "body": "foobarf",
               "json_metadata": ""}
        )
        ops    = [transactions.Operation(op)]
        tx     = transactions.Signed_Transaction(
            ref_block_num=ref_block_num,
            ref_block_prefix=ref_block_prefix,
            expiration=expiration,
            operations=ops
        )
        tx = tx.sign([wif])

        txWire = hexlify(bytes(tx)).decode("ascii")

        compare = "f68585abf4dce7c80457010107666f6f6261726107666f6f6261726207666f6f6261726307666f6f6261726407666f6f6261726507666f6f6261726600011f46428333367ed8a55ab53351c44d08240def16b7942f88dc806c21fb0a72e8063f172d649134df7550111666609b33b382206b14851db58ad07928ed58737663"
        self.assertEqual(compare[:-130], txWire[:-130])

    def test_Vote(self):
        wif              = "5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3"
        ref_block_num    = 34294
        ref_block_prefix = 3707022213
        expiration       = "2016-04-06T08:29:27"

        op = transactions.Vote(
            **{"voter": "foobara",
               "author": "foobarc",
               "permlink": "foobard",
               "weight": 1000}
        )
        ops    = [transactions.Operation(op)]
        tx     = transactions.Signed_Transaction(
            ref_block_num=ref_block_num,
            ref_block_prefix=ref_block_prefix,
            expiration=expiration,
            operations=ops
        )
        tx = tx.sign([wif])

        txWire = hexlify(bytes(tx)).decode("ascii")

        compare = "f68585abf4dce7c80457010007666f6f6261726107666f6f6261726307666f6f62617264e80301202e09123f732a438ef6d6138484d7adedfdcf4a4f3d171f7fcafe836efa2a3c8877290bd34c67eded824ac0cc39e33d154d0617f64af936a83c442f62aef08fec"
        self.assertEqual(compare[:-130], txWire[:-130])
