from steembase import transactions
from graphenebase.account import PrivateKey, PublicKey, Address
import random
import unittest
from pprint import pprint
from binascii import hexlify

wif              = "5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3"
ref_block_num    = 34294
ref_block_prefix = 3707022213
expiration       = "2016-04-06T08:29:27"


class Testcases(unittest.TestCase) :

    def __init__(self, *args, **kwargs):
        super(Testcases, self).__init__(*args, **kwargs)
        self.maxDiff = None

    def test_Comment(self):
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

    def test_Transfer(self):
        op = transactions.Transfer(
            **{"from": "foo",
               "to": "baar",
               "amount": "111.110 STEEM",
               "memo": "Fooo"
               }
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

        compare = "f68585abf4dce7c80457010203666f6f046261617206b201000000000003535445454d000004466f6f6f00012025416c234dd5ff15d8b45486833443c128002bcafa57269cada3ad213ef88adb5831f63a58d8b81bbdd92d494da01eeb13ee1786d02ce075228b25d7132f8f3e"
        self.assertEqual(compare[:-130], txWire[:-130])

    def test_Transfer_to_vesting(self):
        op = transactions.Transfer_to_vesting(
            **{"from": "foo",
               "to": "baar",
               "amount": "111.110 STEEM",
               }
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

        compare = "f68585abf4dce7c80457010303666f6f046261617206b201000000000003535445454d00000001203a34cd45fb4a2585514614be2c1ba2365257ce5470d20c6c6abda39204eeba0b7e057d889ca8b1b1406f1441520a25d32df2ab9fdb532c3377dc66d0fe41bb3d"
        self.assertEqual(compare[:-130], txWire[:-130])

    def test_withdraw_vesting(self):
        op = transactions.Transfer_to_vesting(
            **{"from": "foo",
               "to": "baar",
               "amount": "111.110 STEEM",
               }
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

        compare = "f68585abf4dce7c80457010303666f6f046261617206b201000000000003535445454d00000001203a34cd45fb4a2585514614be2c1ba2365257ce5470d20c6c6abda39204eeba0b7e057d889ca8b1b1406f1441520a25d32df2ab9fdb532c3377dc66d0fe41bb3d"
        self.assertEqual(compare[:-130], txWire[:-130])

    def test_order_create(self):
        op = transactions.Limit_order_create(
            **{"owner": "",
               "orderid": 0,
               "amount_to_sell": "0.000 STEEM",
               "min_to_receive": "0.000 STEEM",
               "fill_or_kill": False,
               "expiration": "2016-12-31T23:59:59"
               }
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
        compare = "f68585abf4dce7c8045701050000000000000000000000000003535445454d0000000000000000000003535445454d0000007f46685800011f28a2fc52dcfc19378c5977917b158dfab93e7760259aab7ecdbcb82df7b22e1a5527e02fd3aab7d64302ec550c3edcbba29d73226cf088273e4fafda89eb7de8"
        self.assertEqual(compare[:-130], txWire[:-130])

    def test_account_update(self):
        op = transactions.Account_update(
            **{"account": "streemian",
                "posting": {
                    "weight_threshold": 1,
                    "account_auths": [["xeroc", 1], ["fabian", 1]],
                    "key_auths": [["STM6KChDK2sns9MwugxkoRvPEnyjuTxHN5upGsZ1EtanCffqBVVX3", 1],
                                  ["STM7sw22HqsXbz7D2CmJfmMwt9rimtk518dRzsR1f8Cgw52dQR1pR", 1]]
                },
                "owner": {
                    "weight_threshold": 1,
                    "account_auths": [],
                    "key_auths": [["STM7sw22HqsXbz7D2CmJfmMwt9rimtk518dRzsR1f8Cgw52dQR1pR", 1],
                                  ["STM6KChDK2sns9MwugxkoRvPEnyjuTxHN5upGsZ1EtanCffqBVVX3", 1]]
                },
                "active": {
                    "weight_threshold": 2,
                    "account_auths": [],
                    "key_auths": [["STM6KChDK2sns9MwugxkoRvPEnyjuTxHN5upGsZ1EtanCffqBVVX3", 1],
                                  ["STM7sw22HqsXbz7D2CmJfmMwt9rimtk518dRzsR1f8Cgw52dQR1pR", 1]]
                },
                "memo_key": "STM728uLvStTeAkYJsQefks3FX8yfmpFHp8wXw3RY3kwey2JGDooR",
                "json_metadata": ""}
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
        compare = "f68585abf4dce7c80457010a0973747265656d69616e0101000000000202bbcf38855c9ae9d55704ee50ff56552af1242266c10544a75b61005e17fa78a601000389d28937022880a7f0c7deaa6f46b4d87ce08bd5149335cb39b5a8e9b04981c201000102000000000202bbcf38855c9ae9d55704ee50ff56552af1242266c10544a75b61005e17fa78a601000389d28937022880a7f0c7deaa6f46b4d87ce08bd5149335cb39b5a8e9b04981c201000101000000020666616269616e0100057865726f6301000202bbcf38855c9ae9d55704ee50ff56552af1242266c10544a75b61005e17fa78a601000389d28937022880a7f0c7deaa6f46b4d87ce08bd5149335cb39b5a8e9b04981c201000318c1ae46b3e98b26684c87737a04ecb1a390efdc7671ced448a92b745372deff000001206a8896c0ce0c949d901c44232694252348004cf9a74ec2f391c0e0b7a4108e7f71522c186a92c17e23a07cdb108a745b9760316daf16f2043453fbeccb331067"
        self.assertEqual(compare[:-130], txWire[:-130])

    def test_order_cancel(self):
        op = transactions.Limit_order_cancel(
            **{"owner": "",
               "orderid": 2141244,
               }
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
        compare = "f68585abf4dce7c804570106003cac20000001206c9888d0c2c31dba1302566f524dfac01a15760b93a8726241a7ae6ba00edfde5b83edaf94a4bd35c2957ded6023576dcbe936338fb9d340e21b5dad6f0028f6"
        self.assertEqual(compare[:-130], txWire[:-130])

    def test_set_route(self):
        op = transactions.Set_withdraw_vesting_route(
            **{"from_account": "xeroc",
               "to_account": "xeroc",
               "percent": 1000,
               "auto_vest": False
               }
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
        compare = "f68585abf4dce7c804570114057865726f63057865726f63e8030000011f12d2b8f93f9528f31979e0e1f59a6d45346a88c02ab2c4115b10c9e273fc1e99621af0c2188598c84762b7e99ca63f6b6be6fca318dd85b0d7a4f09f95579290"
        self.assertEqual(compare[:-130], txWire[:-130])

    def test_convert(self):
        op = transactions.Convert(
            **{"owner": "xeroc",
               "requestid": 2342343235,
               "amount": "100.000 SBD"}
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
        compare = "f68585abf4dce7c804570108057865726f6343529d8ba086010000000000035342440000000000011f3d22eb66e5cddcc90f5d6ca0bd7a43e0ab811ecd480022af8a847c45eac720b342188d55643d8cb1711f516e9879be2fa7dfa329b518f19df4afaaf4f41f7715"
        self.assertEqual(compare[:-130], txWire[:-130])

    def compareConstructedTX(self):
        #    def test_online(self):
        #        self.maxDiff = None
        op = transactions.Convert(
            **{"owner": "xeroc",
               "requestid": 2342343235,
               "amount": "100.000 SBD"}
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

        from grapheneapi.grapheneapi import GrapheneAPI
        rpc = GrapheneAPI("localhost", 8092)
        compare = rpc.serialize_transaction(transactions.JsonObj(tx))

        pprint(transactions.JsonObj(tx))

        print("\n")
        print(compare[:-130])
        print(txWire[:-130])
        print("\n")

        print(txWire[:-130] == compare[:-130])
        self.assertEqual(compare[:-130], txWire[:-130])

if __name__ == '__main__':
    t = Testcases()
    t.compareConstructedTX()
