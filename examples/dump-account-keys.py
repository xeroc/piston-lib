from steemapi.steemwalletrpc import SteemWalletRPC
from pprint import pprint
import time

def dumpkeys(account, typ):
    name = account["name"]
    keys = account[typ]["key_auths"]
    for key in keys:
        wif = rpc.get_private_key(key[0])
        print("%10s: %10s: %s %s" % (
            name, typ, key[0], wif))

rpc = SteemWalletRPC("localhost", 8092, "", "")
accounts = rpc.list_my_accounts()

assert rpc.is_locked, "Wallet is locked"

for account in accounts:
    dumpkeys(account, "active")
    dumpkeys(account, "owner")
    dumpkeys(account, "posting")
