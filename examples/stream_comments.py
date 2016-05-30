from steemapi.steemnoderpc import SteemNodeRPC
from pprint import pprint

rpc = SteemNodeRPC("wss://steemit.com/ws")

for a in rpc.stream("comment", start=1893850):
    pprint(a)
