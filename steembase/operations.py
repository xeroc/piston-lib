import struct
import json
from collections import OrderedDict
from graphenebase.types import (
    Uint8, Int16, Uint16, Uint32, Uint64,
    Varint32, Int64, String, Bytes, Void,
    Array, PointInTime, Signature, Bool,
    Set, Fixed_array, Optional, Static_variant,
    Map, Id, VoteId, ObjectId,
)
from graphenebase.objects import GrapheneObject, isArgsThisClass
from graphenebase.account import PublicKey
from graphenebase.operations import (
    Operation as GrapheneOperation
)
from .operationids import operations
prefix = "STM"
# prefix = "TST"

asset_precision = {
    "STEEM": 3,
    "VESTS": 6,
    "SBD": 3,
    "GOLOS": 3,
    "GESTS": 6,
    "GBG": 3
}


class Operation(GrapheneOperation):
    def __init__(self, op):
        super(Operation, self).__init__(op)

    def operations(self):
        return operations

    def getOperationKlass(self):
        return Operation

    def getOperationNameForId(self, i):
        for key in operations:
            if int(operations[key]) is int(i):
                return key
        return "Unknown Operation ID %d" % i

    def _getklass(self, name):
        module = __import__("steembase.operations", fromlist=["operations"])
        class_ = getattr(module, name)
        return class_

    def __str__(self):
        return json.dumps([
            self.getOperationNameForId(self.opId),
            self.op.json()
        ])


class Permission(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]

            # Sort keys (FIXME: ideally, the sorting is part of Public
            # Key and not located here)
            kwargs["key_auths"] = sorted(
                kwargs["key_auths"],
                key=lambda x: repr(PublicKey(x[0], prefix=prefix)),
                reverse=False,
            )
            kwargs["account_auths"] = sorted(
                kwargs["account_auths"],
                key=lambda x: x[0],
                reverse=False,
            )

            accountAuths = Map([
                [String(e[0]), Uint16(e[1])]
                for e in kwargs["account_auths"]
            ])
            keyAuths = Map([
                [PublicKey(e[0], prefix=prefix), Uint16(e[1])]
                for e in kwargs["key_auths"]
            ])
            super().__init__(OrderedDict([
                ('weight_threshold', Uint32(int(kwargs["weight_threshold"]))),
                ('account_auths', accountAuths),
                ('key_auths', keyAuths),
            ]))


class Memo(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]

            super().__init__(OrderedDict([
                ('from', PublicKey(kwargs["from"], prefix=prefix)),
                ('to', PublicKey(kwargs["to"], prefix=prefix)),
                ('nonce', Uint64(int(kwargs["nonce"]))),
                ('check', Uint32(int(kwargs["check"]))),
                ('encrypted', Bytes(kwargs["encrypted"])),
            ]))


class Vote(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super().__init__(OrderedDict([
                ('voter', String(kwargs["voter"])),
                ('author', String(kwargs["author"])),
                ('permlink', String(kwargs["permlink"])),
                ('weight', Int16(kwargs["weight"])),
            ]))


class Comment(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            meta = ""
            if "json_metadata" in kwargs and kwargs["json_metadata"]:
                if (isinstance(kwargs["json_metadata"], dict) or
                        isinstance(kwargs["json_metadata"], list)):
                    meta = json.dumps(kwargs["json_metadata"])
                else:
                    meta = kwargs["json_metadata"]

            super().__init__(OrderedDict([
                ('parent_author', String(kwargs["parent_author"])),
                ('parent_permlink', String(kwargs["parent_permlink"])),
                ('author', String(kwargs["author"])),
                ('permlink', String(kwargs["permlink"])),
                ('title', String(kwargs["title"])),
                ('body', String(kwargs["body"])),
                ('json_metadata', String(meta)),
            ]))


class Amount():
    def __init__(self, d):
        self.amount, self.asset = d.strip().split(" ")
        self.amount = float(self.amount)

        if self.asset in asset_precision:
            self.precision = asset_precision[self.asset]
        else:
            raise Exception("Asset unknown")

    def __bytes__(self):
        # padding
        asset = self.asset + "\x00" * (7 - len(self.asset))
        amount = round(float(self.amount) * 10 ** self.precision)
        return (
            struct.pack("<q", amount) +
            struct.pack("<b", self.precision) +
            bytes(asset, "ascii")
        )

    def __str__(self):
        return '{:.{}f} {}'.format(
            self.amount,
            self.precision,
            self.asset
        )


class Exchange_rate(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]

            super().__init__(OrderedDict([
                ('base', Amount(kwargs["base"])),
                ('quote', Amount(kwargs["quote"])),
            ]))


class Witness_props(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]

            super().__init__(OrderedDict([
                ('account_creation_fee', Amount(kwargs["account_creation_fee"])),
                ('maximum_block_size', Uint32(kwargs["maximum_block_size"])),
                ('sbd_interest_rate', Uint16(kwargs["sbd_interest_rate"])),
            ]))


########################################################
# Actual Operations
########################################################


class Account_create(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]

            meta = ""
            if "json_metadata" in kwargs and kwargs["json_metadata"]:
                if isinstance(kwargs["json_metadata"], dict):
                    meta = json.dumps(kwargs["json_metadata"])
                else:
                    meta = kwargs["json_metadata"]
            super().__init__(OrderedDict([
                ('fee', Amount(kwargs["fee"])),
                ('creator', String(kwargs["creator"])),
                ('new_account_name', String(kwargs["new_account_name"])),
                ('owner', Permission(kwargs["owner"])),
                ('active', Permission(kwargs["active"])),
                ('posting', Permission(kwargs["posting"])),
                ('memo_key', PublicKey(kwargs["memo_key"], prefix=prefix)),
                ('json_metadata', String(meta)),
            ]))


class Account_update(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]

            meta = ""
            if "json_metadata" in kwargs and kwargs["json_metadata"]:
                if isinstance(kwargs["json_metadata"], dict):
                    meta = json.dumps(kwargs["json_metadata"])
                else:
                    meta = kwargs["json_metadata"]

            owner = Permission(kwargs["owner"]) if "owner" in kwargs else None
            active = Permission(kwargs["active"]) if "active" in kwargs else None
            posting = Permission(kwargs["posting"]) if "posting" in kwargs else None

            super().__init__(OrderedDict([
                ('account', String(kwargs["account"])),
                ('owner', Optional(owner)),
                ('active', Optional(active)),
                ('posting', Optional(posting)),
                ('memo_key', PublicKey(kwargs["memo_key"], prefix=prefix)),
                ('json_metadata', String(meta)),
            ]))


class Transfer(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            if "memo" not in kwargs:
                kwargs["memo"] = ""
            super().__init__(OrderedDict([
                ('from', String(kwargs["from"])),
                ('to', String(kwargs["to"])),
                ('amount', Amount(kwargs["amount"])),
                ('memo', String(kwargs["memo"])),
            ]))


class Transfer_to_vesting(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super().__init__(OrderedDict([
                ('from', String(kwargs["from"])),
                ('to', String(kwargs["to"])),
                ('amount', Amount(kwargs["amount"])),
            ]))


class Withdraw_vesting(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super().__init__(OrderedDict([
                ('account', String(kwargs["account"])),
                ('vesting_shares', Amount(kwargs["vesting_shares"])),
            ]))


class Limit_order_create(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super().__init__(OrderedDict([
                ('owner', String(kwargs["owner"])),
                ('orderid', Uint32(int(kwargs["orderid"]))),
                ('amount_to_sell', Amount(kwargs["amount_to_sell"])),
                ('min_to_receive', Amount(kwargs["min_to_receive"])),
                ('fill_or_kill', Bool(kwargs["fill_or_kill"])),
                ('expiration', PointInTime(kwargs["expiration"])),
            ]))


class Limit_order_cancel(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super().__init__(OrderedDict([
                ('owner', String(kwargs["owner"])),
                ('orderid', Uint32(int(kwargs["orderid"]))),
            ]))


class Set_withdraw_vesting_route(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super().__init__(OrderedDict([
                ('from_account', String(kwargs["from_account"])),
                ('to_account', String(kwargs["to_account"])),
                ('percent', Uint16((kwargs["percent"]))),
                ('auto_vest', Bool(kwargs["auto_vest"])),
            ]))


class Convert(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super().__init__(OrderedDict([
                ('owner', String(kwargs["owner"])),
                ('requestid', Uint32(kwargs["requestid"])),
                ('amount', Amount(kwargs["amount"])),
            ]))


class Feed_publish(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super().__init__(OrderedDict([
                ('publisher', String(kwargs["publisher"])),
                ('exchange_rate', Exchange_rate(kwargs["exchange_rate"])),
            ]))


class Witness_update(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            if not kwargs["block_signing_key"]:
                kwargs["block_signing_key"] = "STM1111111111111111111111111111111114T1Anm"
            super().__init__(OrderedDict([
                ('owner', String(kwargs["owner"])),
                ('url', String(kwargs["url"])),
                ('block_signing_key', PublicKey(kwargs["block_signing_key"], prefix=prefix)),
                ('props', Witness_props(kwargs["props"])),
                ('fee', Amount(kwargs["fee"])),
            ]))


class Transfer_to_savings(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            if "memo" not in kwargs:
                kwargs["memo"] = ""
            super().__init__(OrderedDict([
                ('from', String(kwargs["from"])),
                ('to', String(kwargs["to"])),
                ('amount', Amount(kwargs["amount"])),
                ('memo', String(kwargs["memo"])),
            ]))


class Transfer_from_savings(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            if "memo" not in kwargs:
                kwargs["memo"] = ""

            super().__init__(OrderedDict([
                ('from', String(kwargs["from"])),
                ('request_id', Uint32(int(kwargs["request_id"]))),
                ('to', String(kwargs["to"])),
                ('amount', Amount(kwargs["amount"])),
                ('memo', String(kwargs["memo"])),
            ]))


class Cancel_transfer_from_savings(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super().__init__(OrderedDict([
                ('from', String(kwargs["from"])),
                ('request_id', Uint32(int(kwargs["request_id"]))),
            ]))


class Account_witness_vote(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super().__init__(OrderedDict([
                ('account', String(kwargs["account"])),
                ('witness', String(kwargs["witness"])),
                ('approve', Bool(bool(kwargs["approve"]))),
            ]))


class Custom_json(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            if "json" in kwargs and kwargs["json"]:
                if (isinstance(kwargs["json"], dict) or
                        isinstance(kwargs["json"], list)):
                    js = json.dumps(kwargs["json"])
                else:
                    js = kwargs["json"]

            if len(kwargs["id"]) > 32:
                raise Exception("'id' too long")

            super().__init__(OrderedDict([
                ('required_auths',
                    Array([String(o) for o in kwargs["required_auths"]])),
                ('required_posting_auths',
                    Array([String(o) for o in kwargs["required_posting_auths"]])),
                ('id', String(kwargs["id"])),
                ('json', String(js)),
            ]))
