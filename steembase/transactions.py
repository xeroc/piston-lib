from collections import OrderedDict
from binascii import hexlify, unhexlify
from calendar import timegm
from datetime import datetime
import ecdsa
import hashlib
import json
import struct
import time
from steembase.account import PrivateKey, PublicKey

timeformat = '%Y-%m-%dT%H:%M:%S%Z'

STEEMIT_100_PERCENT = 10000
STEEMIT_1_PERCENT = (STEEMIT_100_PERCENT / 100)

#: Reserved spaces for object ids
reserved_spaces = {}
reserved_spaces["relative_protocol_ids"] = 0
reserved_spaces["protocol_ids"] = 1
reserved_spaces["implementation_ids"] = 2

#: Object types for object ids
object_type = {}
object_type["dynamic_global_property"] = 0
object_type["reserved0"] = 1
object_type["account"] = 2
object_type["witness"] = 3
object_type["transaction"] = 4
object_type["block_summary"] = 5
object_type["chain_property"] = 6
object_type["witness_schedule"] = 7
object_type["comment"] = 8
object_type["category"] = 9
object_type["comment_vote"] = 10
object_type["vote"] = 11
object_type["witness_vote"] = 12
object_type["limit_order"] = 13
object_type["feed_history"] = 14
object_type["convert_request"] = 15
object_type["liquidity_reward_balance"] = 16
object_type["operation"] = 17
object_type["account_history"] = 18

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
operations["fill_convert_request"] = 17
operations["comment_reward"] = 18
operations["curate_reward"] = 19
operations["liquidity_reward"] = 20
operations["interest"] = 21
operations["fill_vesting_withdraw"] = 22
operations["fill_order"] = 23

# : Networks
chain_params = {"chain_id": "0" * int(256 / 4)}


def getOperationNameForId(i) :
    """ Convert an operation id into the corresponding string
    """
    for key in operations :
        if int(operations[key]) is int(i) :
            return key
    return "Unknown Operation ID %d" % i


def varint(n) :
    """ Varint encoding
    """
    data = b''
    while n >= 0x80 :
        data += bytes([(n & 0x7f) | 0x80])
        n >>= 7
    data += bytes([n])
    return data


def varintdecode(data) :
    """ Varint decoding
    """
    shift = 0
    result = 0
    for c in data :
        b = ord(c)
        result |= ((b & 0x7f) << shift)
        if not (b & 0x80) :
            break
        shift += 7
    return result


def variable_buffer(s) :
    """ Encode variable length bugger
    """
    return varint(len(s)) + s


def JsonObj(data) :
    """ Returns json object from data
    """
    return json.loads(str(data))


def isArgsThisClass(self, args):
    return (len(args) == 1 and type(args[0]).__name__ == type(self).__name__)


class Uint8() :
    def __init__(self, d) :
        self.data = d

    def __bytes__(self) :
        return struct.pack("<B", self.data)

    def __str__(self) :
        return '%d' % self.data


class Int16() :
    def __init__(self, d) :
        self.data = d

    def __bytes__(self) :
        return struct.pack("<h", int(self.data))

    def __str__(self) :
        return '%d' % self.data


class Uint16() :
    def __init__(self, d) :
        self.data = d

    def __bytes__(self) :
        return struct.pack("<H", self.data)

    def __str__(self) :
        return '%d' % self.data


class Uint32() :
    def __init__(self, d) :
        self.data = d

    def __bytes__(self) :
        return struct.pack("<I", self.data)

    def __str__(self) :
        return '%d' % self.data


class Uint64() :
    def __init__(self, d) :
        self.data = d

    def __bytes__(self) :
        return struct.pack("<Q", self.data)

    def __str__(self) :
        return '%d' % self.data


class Varint32() :
    def __init__(self, d) :
        self.data = d

    def __bytes__(self) :
        return varint(self.data)

    def __str__(self) :
        return '%d' % self.data


class Int64() :
    def __init__(self, d) :
        self.data = d

    def __bytes__(self) :
        return struct.pack("<q", self.data)

    def __str__(self) :
        return '%d' % self.data


class String() :
    def __init__(self, d) :
        self.data = d

    def __bytes__(self) :
        return varint(len(self.data)) + bytes(self.data, 'utf-8')

    def __str__(self) :
        return '%s' % str(self.data)


class Bytes() :
    def __init__(self, d, length=None) :
        self.data = d
        if length :
            self.length = length
        else :
            self.length = len(self.data)

    def __bytes__(self) :
        d = unhexlify(bytes(self.data, 'utf-8'))
        return varint(len(d)) + d

    def __str__(self) :
        return str(self.data)


class Void() :
    def __init__(self) :
        pass

    def __bytes__(self) :
        return b''

    def __str__(self) :
        return ""


class Array() :
    def __init__(self, d) :
        self.data = d
        self.length = Varint32(len(self.data))

    def __bytes__(self) :
        return bytes(self.length) + b"".join([bytes(a) for a in self.data])

    def __str__(self) :
        return json.dumps([JsonObj(a) for a in self.data])


class PointInTime() :
    def __init__(self, d) :
        self.data = d

    def __bytes__(self) :
        return struct.pack("<I", timegm(time.strptime((self.data + "UTC"), timeformat)))

    def __str__(self) :
        return self.data


class Signature() :
    def __init__(self, d) :
        self.data = d

    def __bytes__(self) :
        return self.data

    def __str__(self) :
        return json.dumps(hexlify(self.data).decode('ascii'))


class Bool(Uint8) :  # Bool = Uint8
    def __init__(self, d) :
        super().__init__(d)


class Set(Array) :  # Set = Array
    def __init__(self, d) :
        super().__init__(d)


class Fixed_array() :
    def __init__(self, d) :
        raise NotImplementedError

    def __bytes__(self) :
        raise NotImplementedError

    def __str__(self) :
        raise NotImplementedError


class Optional() :
    def __init__(self, d) :
        self.data = d

    def __bytes__(self) :
        return bytes(Bool(1)) + bytes(self.data) if bytes(self.data) else bytes(Bool(0))

    def __str__(self) :
        return str(self.data)

    def isempty(self) :
        return not bool(bytes(self.data))


class Static_variant() :
    def __init__(self, d, type_id) :
        self.data = d
        self.type_id = type_id

    def __bytes__(self) :
        return varint(self.type_id) + bytes(self.data)

    def __str__(self) :
        return {self._type_id : str(self.data)}


class Map() :
    def __init__(self, d) :
        raise NotImplementedError

    def __bytes__(self) :
        raise NotImplementedError

    def __str__(self) :
        raise NotImplementedError


class Id() :
    def __init__(self, d) :
        self.data = Varint32(d)

    def __bytes__(self) :
        return bytes(self.data)

    def __str__(self) :
        return str(self.data)


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


class SteemObject(object) :
    """ Core abstraction class

        This class is used for any JSON reflected object in Steem.

        * ``instance.__json__()`` : encodes data into json format
        * ``bytes(instance)`` : encodes data into wire format
        * ``str(instances)`` : dumps json object as string

    """
    def __init__(self, data=None) :
        self.data = data

    def __bytes__(self) :
        if self.data is None :
            return bytes()
        b = b""
        for name, value in self.data.items() :
            if isinstance(value, str) :
                b += bytes(value, 'utf-8')
            else :
                b += bytes(value)
        return b

    def __json__(self) :
        if self.data is None :
            return {}
        d = {}  # JSON output is *not* ordered
        for name, value in self.data.items() :
            if isinstance(value, Optional) and value.isempty() :
                continue
            try :
                d.update({name : JsonObj(value)})
            except :
                d.update({name : str(value)})
        return OrderedDict(d)

    def __str__(self) :
        return json.dumps(self.__json__())


class ObjectId() :
    """ Encodes object/protocol ids
    """
    def __init__(self, object_str, type_verify=None) :
        if len(object_str.split(".")) == 3 :
            space, type, id = object_str.split(".")
            self.space = int(space)
            self.type = int(type)
            self.instance = Id(int(id))
            self.Id = object_str
            if type_verify :
                assert object_type[type_verify] == int(type), "Object id does not match object type!"
        else :
            raise Exception("Object id is invalid")

    def __bytes__(self) :
        return bytes(self.instance)  # only yield instance

    def __str__(self) :
        return self.Id


class Signed_Transaction(SteemObject) :
    """ Create a signed transaction and offer method to create the
        signature

        :param num refNum: parameter ref_block_num (see ``getBlockParams``)
        :param num refPrefix: parameter ref_block_prefix (see ``getBlockParams``)
        :param str expiration: expiration date
        :param Array operations:  array of operations
    """
    def __init__(self, *args, **kwargs) :
        if isArgsThisClass(self, args):
                self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            if "extensions" not in kwargs:
                kwargs["extensions"] = Set([])
            if "signatures" not in kwargs:
                kwargs["signatures"] = Array([])
            else:
                kwargs["signatures"] = Array([Signature(unhexlify(a)) for a in kwargs["signatures"]])

            if "operations" in kwargs:
                if all([not isinstance(a, Operation) for a in kwargs["operations"]]):
                    kwargs['operations'] = Array([Operation(a) for a in kwargs["operations"]])
                else:
                    kwargs['operations'] = Array(kwargs["operations"])

            super().__init__(OrderedDict([
                ('ref_block_num', Uint16(kwargs['ref_block_num'])),
                ('ref_block_prefix', Uint32(kwargs['ref_block_prefix'])),
                ('expiration', PointInTime(kwargs['expiration'])),
                ('operations', kwargs['operations']),
                ('signatures', kwargs['signatures']),
            ]))

    def recoverPubkeyParameter(self, digest, signature, pubkey) :
        """ Use to derive a number that allows to easily recover the
            public key from the signature
        """
        for i in range(0, 4) :
            p = self.recover_public_key(digest, signature, i)
            if p.to_string() == pubkey.to_string() :
                return i
        return None

    def derSigToHexSig(self, s) :
        """ Format DER to HEX signature
        """
        s, junk = ecdsa.der.remove_sequence(unhexlify(s))
        if junk :
            print('JUNK : %s', hexlify(junk).decode('ascii'))
        assert(junk == b'')
        x, s = ecdsa.der.remove_integer(s)
        y, s = ecdsa.der.remove_integer(s)
        return '%064x%064x' % (x, y)

    def recover_public_key(self, digest, signature, i) :
        """ Recover the public key from the the signature
        """
        # See http : //www.secg.org/download/aid-780/sec1-v2.pdf section 4.1.6 primarily
        curve = ecdsa.SECP256k1.curve
        G = ecdsa.SECP256k1.generator
        order = ecdsa.SECP256k1.order
        isYOdd = i % 2
        isSecondKey = i // 2
        yp = 0 if (isYOdd) == 0 else 1
        r, s = ecdsa.util.sigdecode_string(signature, order)
        # 1.1
        x = r + isSecondKey * order
        # 1.3. This actually calculates for either effectively 02||X or 03||X depending on 'k' instead of always for 02||X as specified.
        # This substitutes for the lack of reversing R later on. -R actually is defined to be just flipping the y-coordinate in the elliptic curve.
        alpha = ((x * x * x) + (curve.a() * x) + curve.b()) % curve.p()
        beta = ecdsa.numbertheory.square_root_mod_prime(alpha, curve.p())
        if (beta - yp) % 2 == 0 :
            y = beta
        else :
            y = curve.p() - beta
        # 1.4 Constructor of Point is supposed to check if nR is at infinity.
        R = ecdsa.ellipticcurve.Point(curve, x, y, order)
        # 1.5 Compute e
        e = ecdsa.util.string_to_number(digest)
        # 1.6 Compute Q = r^-1(sR - eG)
        Q = ecdsa.numbertheory.inverse_mod(r, order) * (s * R + (-e % order) * G)
        # Not strictly necessary, but let's verify the message for paranoia's sake.
        if not ecdsa.VerifyingKey.from_public_point(Q, curve=ecdsa.SECP256k1).verify_digest(signature, digest, sigdecode=ecdsa.util.sigdecode_string) :
            return None
        return ecdsa.VerifyingKey.from_public_point(Q, curve=ecdsa.SECP256k1)

    def sign(self, wifkeys, chain="STEEM") :
        """ Sign the transaction with the provided private keys.

            :param array wifkeys: Array of wif keys
            :param str chain: identifier for the chain

        """
        # Get Unique private keys
        self.privkeys = []
        [self.privkeys.append(item) for item in wifkeys if item not in self.privkeys]

        # Chain ID
        self.chainid = chain_params["chain_id"]

        # Get message to sign
        #   bytes(self) will give the wire formated data according to
        #   SteemObject and the data given in __init__()
        self.message = unhexlify(self.chainid) + bytes(self)
        self.digest = hashlib.sha256(self.message).digest()

        # Sign the message with every private key given!
        sigs = []
        for wif in self.privkeys :
            p = bytes(PrivateKey(wif))
            sk = ecdsa.SigningKey.from_string(p, curve=ecdsa.SECP256k1)
            cnt = 0
            i = 0
            while 1 :
                cnt += 1
                if not cnt % 20 :
                    print("Still searching for a canonical signature. Tried %d times already!" % cnt)

                # Deterministic k
                #
                k = ecdsa.rfc6979.generate_k(
                    sk.curve.generator.order(),
                    sk.privkey.secret_multiplier,
                    hashlib.sha256,
                    hashlib.sha256(self.digest + (b'%x' % cnt)).digest())

                # Sign message
                #
                sigder = sk.sign_digest(
                    self.digest,
                    sigencode=ecdsa.util.sigencode_der,
                    k=k)

                # Reformating of signature
                #
                r, s = ecdsa.util.sigdecode_der(sigder, sk.curve.generator.order())
                signature = ecdsa.util.sigencode_string(r, s, sk.curve.generator.order())

                # Make sure signature is canonical!
                #
                lenR = sigder[3]
                lenS = sigder[5 + lenR]
                if lenR is 32 and lenS is 32 :
                    # Derive the recovery parameter
                    #
                    i = self.recoverPubkeyParameter(self.digest, signature, sk.get_verifying_key())
                    i += 4   # compressed
                    i += 27  # compact
                    break

            # pack signature
            #
            sigstr = struct.pack("<B", i)
            sigstr += signature

            sigs.append(Signature(sigstr))

        self.data["signatures"] = Array(sigs)
        return self

"""##############################################################
         Auxiliary calls that require a websocket connection!
##############################################################"""


def getBlockParams(ws) :
    """ Auxiliary method to obtain ``ref_block_num`` and
        ``ref_block_prefix``. Requires a websocket connection to a
        witness node!
    """
    dynBCParams = ws.get_dynamic_global_properties()
    ref_block_num = dynBCParams["head_block_number"] & 0xFFFF
    ref_block_prefix = struct.unpack_from("<I", unhexlify(dynBCParams["head_block_id"]), 4)[0]
    return ref_block_num, ref_block_prefix

"""##############################################################
         Other auxiliary calls
##############################################################"""


def formatTimeFromNow(secs=0) :
    """ Properly Format Time that is `x` seconds in the future

     :param int secs: Seconds to go in the future (`x>0`) or the past (`x<0`)
     :return: Properly formated time for Steem (`%Y-%m-%dT%H:%M:%S`)
     :rtype: str

    """
    return datetime.utcfromtimestamp(time.time() + int(secs)).strftime(timeformat)


"""
             O P E R A T I O N S
"""


class Vote(SteemObject) :
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


class Comment(SteemObject) :
    def __init__(self, *args, **kwargs) :
        if isArgsThisClass(self, args):
                self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super().__init__(OrderedDict([
                ('parent_author'   , String(kwargs["parent_author"])),
                ('parent_permlink' , String(kwargs["parent_permlink"])),
                ('author'          , String(kwargs["author"])),
                ('permlink'        , String(kwargs["permlink"])),
                ('title'           , String(kwargs["title"])),
                ('body'            , String(kwargs["body"])),
                ('json_metadata'   , String(kwargs["json_metadata"])),
            ]))
