from steembase import transactions
from graphenebase.account import PrivateKey, PublicKey, Address
import random
import unittest
from pprint import pprint
from binascii import hexlify


class Testcases(unittest.TestCase) :

    def __init__(self, *args, **kwargs):
        super(Testcases, self).__init__(*args, **kwargs)
        self.maxDiff = None

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

        compare = "f68585abf4dce7c80457010107666f6f6261726107666f6f6261726207666f6f6261726307666f6f6261726407666f6f6261726507666f6f626172660000011f46428333367ed8a55ab53351c44d08240def16b7942f88dc806c21fb0a72e8063f172d649134df7550111666609b33b382206b14851db58ad07928ed58737663"
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

        tx.verify([PrivateKey(wif).pubkey])

        txWire = hexlify(bytes(tx)).decode("ascii")

        compare = "f68585abf4dce7c80457010007666f6f6261726107666f6f6261726307666f6f62617264e8030001202e09123f732a438ef6d6138484d7adedfdcf4a4f3d171f7fcafe836efa2a3c8877290bd34c67eded824ac0cc39e33d154d0617f64af936a83c442f62aef08fec"
        self.assertEqual(compare[:-130], txWire[:-130])

    def test_create_account(self):
        wif              = "5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3"
        ref_block_num    = 34294
        ref_block_prefix = 3707022213
        expiration       = "2016-04-06T08:29:27"

        op = transactions.Account_create(
            **{'active': {'account_auths': [],
                        'key_auths': [['STM6pbVDAjRFiw6fkiKYCrkz7PFeL7XNAfefrsREwg8MKpJ9VYV9x',
                                       1]],
                        'weight_threshold': 1},
             'creator': 'xeroc',
             'fee': '10.000 STEEM',
             'json_metadata': '',
             'memo_key': 'STM6zLNtyFVToBsBZDsgMhgjpwysYVbsQD6YhP3kRkQhANUB4w7Qp',
             'new_account_name': 'fsafaasf',
             'owner': {'account_auths': [],
                       'key_auths': [['STM5jYVokmZHdEpwo5oCG3ES2Ca4VYzy6tM8pWWkGdgVnwo2mFLFq',
                                      1]],
                       'weight_threshold': 1},
             'posting': {'account_auths': [],
                         'key_auths': [['STM8CemMDjdUWSV5wKotEimhK6c4dY7p2PdzC2qM1HpAP8aLtZfE7',
                                        1]],
                         'weight_threshold': 1}}
        )
        ops = [transactions.Operation(op)]
        tx = transactions.Signed_Transaction(
            ref_block_num=ref_block_num,
            ref_block_prefix=ref_block_prefix,
            expiration=expiration,
            operations=ops
        )
        tx = tx.sign([wif])

        txWire = hexlify(bytes(tx)).decode("ascii")

        compare = "f68585abf4dce7c804570109102700000000000003535445454d0000057865726f63086673616661617366010000000001026f6231b8ed1c5e964b42967759757f8bb879d68e7b09d9ea6eedec21de6fa4c4010001000000000102fe8cc11cc8251de6977636b55c1ab8a9d12b0b26154ac78e56e7c4257d8bcf69010001000000000103b453f46013fdbccb90b09ba169c388c34d84454a3b9fbec68d5a7819a734fca001000314aa202c9158990b3ec51a1aa49b2ab5d300c97b391df3beb34bb74f3c62699e0000011f1e849e5e25bb40e7ae286028d97f91f825d4366af63eb719d0b317c92a8bfd8240ceb08153777924a5f53103372cd7ce37162dc535c9aef8bc4d61fabbae0bd3"
        self.assertEqual(compare[:-130], txWire[:-130])

if __name__ == '__main__':
        #    def test_online(self):
        #        self.maxDiff = None
        prefix           = "STEEM"
        wif              = "5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3"

        from grapheneapi.grapheneapi import GrapheneAPI
        rpc = GrapheneAPI("localhost", 8092)
        tx = rpc.create_account("xeroc", "fsafaasf", "", False)
        pprint(tx)
        compare = rpc.serialize_transaction(tx)
        ref_block_num    = tx["ref_block_num"]
        ref_block_prefix = tx["ref_block_prefix"]
        expiration       = tx["expiration"]

        ops    = [transactions.Operation(transactions.Account_create(**tx["operations"][0][1]))]
        tx     = transactions.Signed_Transaction(ref_block_num=ref_block_num,
                                                 ref_block_prefix=ref_block_prefix,
                                                 expiration=expiration,
                                                 operations=ops)
        tx     = tx.sign([wif], chain=prefix)
        txWire = hexlify(bytes(tx)).decode("ascii")
        print("\n")
        print(txWire[:-130])
        print(compare[:-130])
        self.assertEqual(compare[:-130], txWire[:-130])
