from steemapi.steemclient import SteemClient
from prettytable import PrettyTable
from textwrap import wrap


class Config():
    wallet_host           = "localhost"
    wallet_port           = 8092
    witness_url           = "ws://localhost:8090"


def dumpMessages(contents):
    t = PrettyTable(["Author", "Permlink", "Subject", "Body"])
    t.align = "l"
    for s in contents:
        content = contents[s]
        t.add_row([
            content["author"],
            content["permlink"],
            "\n".join(wrap(content["title"], 40)),
            "\n".join(wrap(content["body"], 60))
        ])
    print(t.get_string())

if __name__ == '__main__':
    client = SteemClient(Config)
    state = client.rpc.get_state("")
    dumpMessages(state["content"])
