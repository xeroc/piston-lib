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
               "json_metadata": {"foo": "bar"}}
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

        compare = "f68585abf4dce7c80457010107666f6f6261726107666f6f6261726207666f6f6261726307666f6f6261726407666f6f6261726507666f6f626172660e7b22666f6f223a2022626172227d00011f34a882f3b06894c29f52e06b8a28187b84b817c0e40f124859970b32511a778736d682f24d3a6e6da124b340668d25bbcf85ffa23ca622b307ffe10cf182bb82"
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
            **{'creator': 'xeroc',
               'fee': '10.000 STEEM',
               'json_metadata': '',
               'memo_key': 'STM6zLNtyFVToBsBZDsgMhgjpwysYVbsQD6YhP3kRkQhANUB4w7Qp',
               'new_account_name': 'fsafaasf',
               'owner': {'account_auths': [],
                         'key_auths': [['STM5jYVokmZHdEpwo5oCG3ES2Ca4VYzy6tM8pWWkGdgVnwo2mFLFq',
                                        1], [
                                       'STM6zLNtyFVToBsBZDsgMhgjpwysYVbsQD6YhP3kRkQhANUB4w7Qp',
                                       1]],
                         'weight_threshold': 1},
               'active': {'account_auths': [],
                          'key_auths': [['STM6pbVDAjRFiw6fkiKYCrkz7PFeL7XNAfefrsREwg8MKpJ9VYV9x',
                                        1], [
                                        'STM6zLNtyFVToBsBZDsgMhgjpwysYVbsQD6YhP3kRkQhANUB4w7Qp',
                                        1]],
                          'weight_threshold': 1},
               'posting': {'account_auths': [],
                           'key_auths': [['STM8CemMDjdUWSV5wKotEimhK6c4dY7p2PdzC2qM1HpAP8aLtZfE7',
                                          1], [
                                         'STM6zLNtyFVToBsBZDsgMhgjpwysYVbsQD6YhP3kRkQhANUB4w7Qp',
                                         1], [
                                         'STM6pbVDAjRFiw6fkiKYCrkz7PFeL7XNAfefrsREwg8MKpJ9VYV9x',
                                         1
                                         ]],
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

        compare = "f68585abf4dce7c804570109102700000000000003535445454d0000057865726f63086673616661617366010000000002026f6231b8ed1c5e964b42967759757f8bb879d68e7b09d9ea6eedec21de6fa4c401000314aa202c9158990b3ec51a1aa49b2ab5d300c97b391df3beb34bb74f3c62699e010001000000000202fe8cc11cc8251de6977636b55c1ab8a9d12b0b26154ac78e56e7c4257d8bcf6901000314aa202c9158990b3ec51a1aa49b2ab5d300c97b391df3beb34bb74f3c62699e010001000000000302fe8cc11cc8251de6977636b55c1ab8a9d12b0b26154ac78e56e7c4257d8bcf6901000314aa202c9158990b3ec51a1aa49b2ab5d300c97b391df3beb34bb74f3c62699e010003b453f46013fdbccb90b09ba169c388c34d84454a3b9fbec68d5a7819a734fca001000314aa202c9158990b3ec51a1aa49b2ab5d300c97b391df3beb34bb74f3c62699e0000012031827ea70b06e413d124d14ed8db399597fa5f94566e031b706533a9090395be1c0ed317c8af01d12ca79258ac4d800adff92a84630b567e5ff48cd4b5f716d6"
        self.assertEqual(compare[:-130], txWire[:-130])

    def compareConstructedTX(self):
        #    def test_online(self):
        #        self.maxDiff = None
        wif              = "5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3"
        ref_block_num    = 34294
        ref_block_prefix = 3707022213
        expiration       = "2016-04-06T08:29:27"

        op = transactions.Account_create(
            **{'creator': 'xeroc',
               'fee': '10.000 STEEM',
               'json_metadata': '',
               'memo_key': 'STM6zLNtyFVToBsBZDsgMhgjpwysYVbsQD6YhP3kRkQhANUB4w7Qp',
               'new_account_name': 'fsafaasf',
               'owner': {'account_auths': [],
                         'key_auths': [['STM5jYVokmZHdEpwo5oCG3ES2Ca4VYzy6tM8pWWkGdgVnwo2mFLFq',
                                        1], [
                                       'STM6zLNtyFVToBsBZDsgMhgjpwysYVbsQD6YhP3kRkQhANUB4w7Qp',
                                       1]],
                         'weight_threshold': 1},
               'active': {'account_auths': [],
                          'key_auths': [['STM6pbVDAjRFiw6fkiKYCrkz7PFeL7XNAfefrsREwg8MKpJ9VYV9x',
                                        1], [
                                        'STM6zLNtyFVToBsBZDsgMhgjpwysYVbsQD6YhP3kRkQhANUB4w7Qp',
                                        1]],
                          'weight_threshold': 1},
               'posting': {'account_auths': [],
                           'key_auths': [['STM8CemMDjdUWSV5wKotEimhK6c4dY7p2PdzC2qM1HpAP8aLtZfE7',
                                          1], [
                                         'STM6zLNtyFVToBsBZDsgMhgjpwysYVbsQD6YhP3kRkQhANUB4w7Qp',
                                         1], [
                                         'STM6pbVDAjRFiw6fkiKYCrkz7PFeL7XNAfefrsREwg8MKpJ9VYV9x',
                                         1
                                         ]],
                           'weight_threshold': 1}}
        )

        ops = [transactions.Operation(op)]
        tx = transactions.Signed_Transaction(
            ref_block_num=ref_block_num,
            ref_block_prefix=ref_block_prefix,
            expiration=expiration,
            operations=ops
        )
        pprint(transactions.JsonObj(tx))
        print(bytes(tx))
        tx = tx.sign([wif])
        txWire = hexlify(bytes(tx)).decode("ascii")
        pprint(transactions.JsonObj(tx))

        from grapheneapi.grapheneapi import GrapheneAPI
        rpc = GrapheneAPI("localhost", 8092)
        compare = rpc.serialize_transaction(transactions.JsonObj(tx))

        print("\n")
        print(txWire[:-130])
        print(compare[:-130])
        print("\n")

        print(txWire[:-130] == compare[:-130])
        self.assertEqual(compare[:-130], txWire[:-130])

    def compareNewWire(self):
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
        # self.assertEqual(compare[:-130], txWire[:-130])

if __name__ == '__main__':
    t = Testcases()
    t.compareConstructedTX()
