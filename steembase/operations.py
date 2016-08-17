import json
from graphenebase.types import *
from graphenebase.objects import GrapheneObject, isArgsThisClass
from graphenebase.account import PublicKey, Address

#: Operation ids
operations = {}
operations["vote"] = 0
operations["comment"] = 1
operations["transfer"] = 2
operations["transfer_to_vesting"] = 3
operations["withdraw_vesting"] = 4
operations["limit_order_create"] = 5
operations["limit_order_cancel"] = 6
operations["feed_publish"] = 7
operations["convert"] = 8
operations["account_create"] = 9
operations["account_update"] = 10
operations["witness_update"] = 11
operations["account_witness_vote"] = 12
operations["account_witness_proxy"] = 13
operations["pow"] = 14
operations["custom"] = 15
operations["report_over_production"] = 16
operations["delete_comment"] = 17
operations["custom_json"] = 18
operations["comment_options"] = 19
operations["set_withdraw_vesting_route"] = 20
operations["limit_order_create2"] = 22
operations["challenge_authority"] = 23
operations["prove_authority"] = 24
operations["request_account_recovery"] = 25
operations["recover_account"] = 26
operations["change_recovery_account"] = 27
operations["escrow_transfer"] = 28
operations["escrow_dispute"] = 29
operations["escrow_release"] = 30
# virtual operations below this point"
#operations["fill_convert_request"] = 0
#operations["comment_reward"] = 0
#operations["curate_reward"] = 0
#operations["liquidity_reward"] = 0
#operations["interest"] = 0
#operations["fill_vesting_withdraw"] = 0
#operations["fill_order"] = 0
#operations["comment_payout"] = 0

prefix = "STM"
# prefix = "TST"


def getOperationNameForId(i) :
    """ Convert an operation id into the corresponding string
    """
    for key in operations :
        if int(operations[key]) is int(i) :
            return key
    return "Unknown Operation ID %d" % i


class Operation() :
    def __init__(self, op) :
        if isinstance(op, list) and len(op) == 2:
            self.opId = operations[op[0]]
            name = op[0]
            self.name = name[0].upper() + name[1:]
            try:
                klass = eval(self.name)
            except:
                raise NotImplementedError("Unimplemented Operation %s" % self.name)
            self.op = klass(op[1])
        else:
            self.op = op
            self.name = type(self.op).__name__.lower()  # also store name
            self.opId = operations[self.name]

    def __bytes__(self) :
        return bytes(Id(self.opId)) + bytes(self.op)

    def __str__(self) :
        return json.dumps([getOperationNameForId(self.opId), JsonObj(self.op)])


class Permission(GrapheneObject):
    def __init__(self, *args, **kwargs) :
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
                ('account_auths'   , accountAuths),
                ('key_auths'       , keyAuths),
            ]))


class Memo(GrapheneObject) :
    def __init__(self, *args, **kwargs) :
        if isArgsThisClass(self, args):
                self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]

            super().__init__(OrderedDict([
                ('from'      , PublicKey(kwargs["from"], prefix=prefix)),
                ('to'        , PublicKey(kwargs["to"], prefix=prefix)),
                ('nonce'     , Uint64(int(kwargs["nonce"]))),
                ('check'     , Uint32(int(kwargs["check"]))),
                ('encrypted' , Bytes(kwargs["encrypted"])),
            ]))

"""
    Actual Operations
"""


class Vote(GrapheneObject) :
    def __init__(self, *args, **kwargs) :
        if isArgsThisClass(self, args):
                self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super().__init__(OrderedDict([
                ('voter'    , String(kwargs["voter"])),
                ('author'   , String(kwargs["author"])),
                ('permlink' , String(kwargs["permlink"])),
                ('weight'   , Int16(kwargs["weight"])),
            ]))


class Comment(GrapheneObject) :
    def __init__(self, *args, **kwargs) :
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
                ('parent_author'   , String(kwargs["parent_author"])),
                ('parent_permlink' , String(kwargs["parent_permlink"])),
                ('author'          , String(kwargs["author"])),
                ('permlink'        , String(kwargs["permlink"])),
                ('title'           , String(kwargs["title"])),
                ('body'            , String(kwargs["body"])),
                ('json_metadata'   , String(meta)),
            ]))


class Amount() :
    def __init__(self, d) :
        self.amount, self.asset = d.strip().split(" ")
        self.amount = float(self.amount)

        if self.asset == "STEEM":
            self.precision = 3
        elif self.asset == "VESTS":
            self.precision = 6
        elif self.asset == "SBD":
            self.precision = 3
        else:
            raise Exception("Asset unknown")

    def __bytes__(self) :
        # padding
        asset = self.asset + "\x00" * (7 - len(self.asset))
        amount = round(float(self.amount) * 10 ** self.precision)
        return struct.pack("<q", amount) + \
            struct.pack("<b", self.precision) + \
            bytes(asset, "ascii")

    def __str__(self) :
        return '{:.{}f} {}'.format(
            self.amount,
            self.precision,
            self.asset
        )


class Account_create(GrapheneObject) :
    def __init__(self, *args, **kwargs) :
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
                ('fee'              , Amount(kwargs["fee"])),
                ('creator'          , String(kwargs["creator"])),
                ('new_account_name' , String(kwargs["new_account_name"])),
                ('owner'            , Permission(kwargs["owner"])),
                ('active'           , Permission(kwargs["active"])),
                ('posting'          , Permission(kwargs["posting"])),
                ('memo_key'         , PublicKey(kwargs["memo_key"], prefix=prefix)),
                ('json_metadata'    , String(meta)),
            ]))


class Account_update(GrapheneObject) :
    def __init__(self, *args, **kwargs) :
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
                ('account'          , String(kwargs["account"])),
                ('owner'            , Optional(owner)),
                ('active'           , Optional(active)),
                ('posting'          , Optional(posting)),
                ('memo_key'         , PublicKey(kwargs["memo_key"], prefix=prefix)),
                ('json_metadata'    , String(meta)),
            ]))


class Transfer(GrapheneObject) :
    def __init__(self, *args, **kwargs) :
        if isArgsThisClass(self, args):
                self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            if "memo" not in kwargs:
                kwargs["memo"] = ""
            super().__init__(OrderedDict([
                ('from'          , String(kwargs["from"])),
                ('to'            , String(kwargs["to"])),
                ('amount'        , Amount(kwargs["amount"])),
                ('memo'          , String(kwargs["memo"])),
            ]))


class Transfer_to_vesting(GrapheneObject) :
    def __init__(self, *args, **kwargs) :
        if isArgsThisClass(self, args):
                self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super().__init__(OrderedDict([
                ('from'          , String(kwargs["from"])),
                ('to'            , String(kwargs["to"])),
                ('amount'        , Amount(kwargs["amount"])),
            ]))


class Withdraw_vesting(GrapheneObject) :
    def __init__(self, *args, **kwargs) :
        if isArgsThisClass(self, args):
                self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super().__init__(OrderedDict([
                ('account'          , String(kwargs["account"])),
                ('vesting_shares'   , Amount(kwargs["vesting_shares"])),
            ]))


class Limit_order_create(GrapheneObject) :
    def __init__(self, *args, **kwargs) :
        if isArgsThisClass(self, args):
                self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super().__init__(OrderedDict([
                ('owner'          , String(kwargs["owner"])),
                ('orderid'        , Uint32(int(kwargs["orderid"]))),
                ('amount_to_sell' , Amount(kwargs["amount_to_sell"])),
                ('min_to_receive' , Amount(kwargs["min_to_receive"])),
                ('fill_or_kill'   , Bool(kwargs["fill_or_kill"])),
                ('expiration'     , PointInTime(kwargs["expiration"])),
            ]))


class Limit_order_cancel(GrapheneObject) :
    def __init__(self, *args, **kwargs) :
        if isArgsThisClass(self, args):
                self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super().__init__(OrderedDict([
                ('owner'          , String(kwargs["owner"])),
                ('orderid'        , Uint32(int(kwargs["orderid"]))),
            ]))


class Set_withdraw_vesting_route(GrapheneObject) :
    def __init__(self, *args, **kwargs) :
        if isArgsThisClass(self, args):
                self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super().__init__(OrderedDict([
                ('from_account'   , String(kwargs["from_account"])),
                ('to_account'     , String(kwargs["to_account"])),
                ('percent'        , Uint16((kwargs["percent"]))),
                ('auto_vest'      , Bool(kwargs["auto_vest"])),
            ]))


class Convert(GrapheneObject) :
    def __init__(self, *args, **kwargs) :
        if isArgsThisClass(self, args):
                self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super().__init__(OrderedDict([
                ('owner'      , String(kwargs["owner"])),
                ('requestid'  , Uint32(kwargs["requestid"])),
                ('amount'     , Amount(kwargs["amount"])),
            ]))
