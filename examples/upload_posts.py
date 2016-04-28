from steemapi.steemclient import SteemClient
from pprint import pprint
from prettytable import PrettyTable
from textwrap import wrap
from os import walk, path
import argparse


class Config():
    wallet_host           = "localhost"
    wallet_port           = 8092
    witness_url           = "ws://localhost:8090"

def print_help():
    pass

def main() :
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=("Post files into STEEM\n\n"
                "This script goes into the posts directory that "
                "contains subfolders named after the authors.\n"
                "This subfolders contain markdown (*.md) files "
                "from which \n"
                "   * the file name is used as permlink\n"
                "   * the first line of content is subject\n"
                "   * the rest of the content is body\n")
    )
    parser.add_argument('--author',
                        type=str,
                        help='Only publish/update posts of this author')
    parser.add_argument('--permlink',
                        type=str,
                        help='Only publish/update the permlink')
    parser.add_argument('--category',
                        type=str,
                        help='Post in category')
    parser.add_argument('--dir',
                        type=str,
                        help='Directory that holds all posts (default: "posts")')
    parser.add_argument('-d',
                        "--dryrun",
                        help="Not not actually post anything",
                        action="store_true")
    parser.set_defaults(dir="./posts", dryrun=False, category="")
    args = parser.parse_args()

    if not path.isdir(args.dir):
        raise Exception("Directory %s does not exist!" % args.dir)
        
    try:
        client = SteemClient(Config)
    except:
        raise Exception("Coudn't open conenction to wallet!")

    if client.wallet.is_locked():
        raise Exception("Wallet is locked! Please unlock it!")

    for (dirpath, dirnames, filenames) in walk(args.dir):
        for f in filenames:
            author = dirpath.split("/")[-1]
            permlink = f.replace(".md", "")
            if args.author and author != args.author:
                continue
            if args.permlink and permlink != args.permlink:
                continue

            content = open(dirpath + "/" + f).read().split("\n")
            subject = content[0].replace("# ", "")
            body = "\n".join(content[2:])

            pprint(client.wallet.post_comment(author,
                                              permlink,
                                              "", args.category,
                                              subject,
                                              body,
                                              "{}",
                                              not args.dryrun))

if __name__ == '__main__':
    main()
