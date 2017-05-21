import json
import logging
import random
import re
from datetime import datetime, timedelta

import pkg_resources  # part of setuptools
from pistonapi.steemnoderpc import SteemNodeRPC, NoAccessApi
from pistonbase import memo
from pistonbase import operations
from pistonbase.account import PrivateKey, PublicKey

from .account import Account
from .amount import Amount
from .blockchain import Blockchain
from .exceptions import (
    AccountExistsException,
    MissingKeyError,
)
from .post import (
    Post
)
from .storage import configStorage as config
from .transactionbuilder import TransactionBuilder
from .utils import (
    resolveIdentifier,
    constructIdentifier,
    derivePermlink,
    formatTimeString
)
from .wallet import Wallet

log = logging.getLogger(__name__)

STEEMIT_100_PERCENT = 10000
STEEMIT_1_PERCENT = (STEEMIT_100_PERCENT / 100)


class Steem(object):
    """ Connect to the Steem network.

        :param str node: Node to connect to *(optional)*
        :param str rpcuser: RPC user *(optional)*
        :param str rpcpassword: RPC password *(optional)*
        :param bool nobroadcast: Do **not** broadcast a transaction! *(optional)*
        :param bool debug: Enable Debugging *(optional)*
        :param array,dict,string keys: Predefine the wif keys to shortcut the wallet database
        :param bool offline: Boolean to prevent connecting to network (defaults to ``False``)

        Three wallet operation modes are possible:

        * **Wallet Database**: Here, the steemlibs load the keys from the
          locally stored wallet SQLite database (see ``storage.py``).
          To use this mode, simply call ``Steem()`` without the
          ``keys`` parameter
        * **Providing Keys**: Here, you can provide the keys for
          your accounts manually. All you need to do is add the wif
          keys for the accounts you want to use as a simple array
          using the ``keys`` parameter to ``Steem()``.
        * **Force keys**: This more is for advanced users and
          requires that you know what you are doing. Here, the
          ``keys`` parameter is a dictionary that overwrite the
          ``active``, ``owner``, ``posting`` or ``memo`` keys for
          any account. This mode is only used for *foreign*
          signatures!

        If no node is provided, it will connect to the node of
        http://piston.rocks. It is **highly** recommended that you pick your own
        node instead. Default settings can be changed with:

        .. code-block:: python

            piston set node <host>

        where ``<host>`` starts with ``ws://`` or ``wss://``.

        The purpose of this class it to simplify posting and dealing
        with accounts, posts and categories in Steem.

        The idea is to have a class that allows to do this:

        .. code-block:: python

            from piston import Steem
            steem = Steem()
            steem.post("Testing steem library", "I am testing steem", category="spam")

        All that is requires is for the user to have added a posting key with piston

        .. code-block:: bash

            piston addkey

        and setting a default author:

        .. code-block:: bash

            piston set default_author xeroc

        This class also deals with edits, votes and reading content.
    """

    def __init__(self,
                 node="",
                 rpcuser="",
                 rpcpassword="",
                 debug=False,
                 **kwargs):

        # More specific set of APIs to register to
        if "apis" not in kwargs:
            kwargs["apis"] = [
                "database",
                "network_broadcast",
            ]

        self.rpc = None
        self.debug = debug

        self.offline = kwargs.get("offline", False)
        self.nobroadcast = kwargs.get("nobroadcast", False)
        self.unsigned = kwargs.get("unsigned", False)
        self.expiration = int(kwargs.get("expiration", 30))

        if not self.offline:
            self._connect(node=node,
                          rpcuser=rpcuser,
                          rpcpassword=rpcpassword,
                          **kwargs)

        # Try Optional APIs
        try:
            self.rpc.register_apis(["account_by_key", "follow"])
        except NoAccessApi as e:
            log.info(str(e))

        self.wallet = Wallet(self.rpc, **kwargs)

    def _connect(self,
                 node="",
                 rpcuser="",
                 rpcpassword="",
                 **kwargs):
        """ Connect to Steem network (internal use only)
        """
        if not node:
            if "node" in config:
                node = config["node"]
            else:
                raise ValueError("A Steem node needs to be provided!")

        if not rpcuser and "rpcuser" in config:
            rpcuser = config["rpcuser"]

        if not rpcpassword and "rpcpassword" in config:
            rpcpassword = config["rpcpassword"]

        self.rpc = SteemNodeRPC(node, rpcuser, rpcpassword, **kwargs)

    def finalizeOp(self, ops, account, permission):
        """ This method obtains the required private keys if present in
            the wallet, finalizes the transaction, signs it and
            broadacasts it

            :param operation ops: The operation (or list of operaions) to broadcast
            :param operation account: The account that authorizes the
                operation
            :param string permission: The required permission for
                signing (active, owner, posting)

            ... note::

                If ``ops`` is a list of operation, they all need to be
                signable by the same key! Thus, you cannot combine ops
                that require active permission with ops that require
                posting permission. Neither can you use different
                accounts for different operations!
        """
        tx = TransactionBuilder(steem_instance=self)
        tx.appendOps(ops)

        if self.unsigned:
            tx.addSigningInformation(account, permission)
            return tx
        else:
            tx.appendSigner(account, permission)
            tx.sign()

        return tx.broadcast()

    def sign(self, tx, wifs=[]):
        """ Sign a provided transaction witht he provided key(s)

            :param dict tx: The transaction to be signed and returned
            :param string wifs: One or many wif keys to use for signing
                a transaction. If not present, the keys will be loaded
                from the wallet as defined in "missing_signatures" key
                of the transactions.
        """
        tx = TransactionBuilder(tx, steem_instance=self)
        tx.appendMissingSignatures(wifs)
        tx.sign()
        return tx.json()

    def broadcast(self, tx):
        """ Broadcast a transaction to the Steem network

            :param tx tx: Signed transaction to broadcast
        """
        tx = TransactionBuilder(tx, steem_instance=self)
        return tx.broadcast()

    def symbol(self, asset):
        """ This method returns the symbol names used on the blockchain.
            It is only relevant if we are not on STEEM, but e.g. on
            GOLOS
        """
        assert asset.lower() in ["sbd", "steem"]
        return self.rpc.chain_params["%s_symbol" % asset.lower()]

    def info(self):
        """ Returns the global properties
        """
        return self.rpc.get_dynamic_global_properties()

    def reply(self, identifier, body, title="", author="", meta=None):
        """ Reply to an existing post

            :param str identifier: Identifier of the post to reply to. Takes the
                             form ``@author/permlink``
            :param str body: Body of the reply
            :param str title: Title of the reply post
            :param str author: Author of reply (optional) if not provided
                               ``default_user`` will be used, if present, else
                               a ``ValueError`` will be raised.
            :param json meta: JSON meta object that can be attached to the
                              post. (optional)
        """
        return self.post(title,
                         body,
                         meta=meta,
                         author=author,
                         reply_identifier=identifier)

    def edit(self,
             identifier,
             body,
             meta={},
             replace=False):
        """ Edit an existing post

            :param str identifier: Identifier of the post to reply to. Takes the
                             form ``@author/permlink``
            :param str body: Body of the reply
            :param json meta: JSON meta object that can be attached to the
                              post. (optional)
            :param bool replace: Instead of calculating a *diff*, replace
                                 the post entirely (defaults to ``False``)
        """
        original_post = Post(identifier, steem_instance=self)

        if replace:
            newbody = body
        else:
            import diff_match_patch
            dmp = diff_match_patch.diff_match_patch()
            patch = dmp.patch_make(original_post["body"], body)
            newbody = dmp.patch_toText(patch)

            if not newbody:
                log.info("No changes made! Skipping ...")
                return

        reply_identifier = constructIdentifier(
            original_post["parent_author"],
            original_post["parent_permlink"]
        )

        new_meta = {}
        if meta:
            if original_post["json_metadata"]:
                import json
                new_meta = original_post["json_metadata"].update(meta)
            else:
                new_meta = meta

        return self.post(
            original_post["title"],
            newbody,
            reply_identifier=reply_identifier,
            author=original_post["author"],
            permlink=original_post["permlink"],
            meta=new_meta,
        )

    def post(self,
             title,
             body,
             author=None,
             permlink=None,
             meta={},
             reply_identifier=None,
             category=None,
             tags=[]):
        """ New post

            :param str title: Title of the reply post
            :param str body: Body of the reply
            :param str author: Author of reply (optional) if not provided
                               ``default_user`` will be used, if present, else
                               a ``ValueError`` will be raised.
            :param json meta: JSON meta object that can be attached to the
                              post. This can be used to add ``tags`` or ``options``.
                              The default options are:::

                                   {
                                        "author": "",
                                        "permlink": "",
                                        "max_accepted_payout": "1000000.000 SBD",
                                        "percent_steem_dollars": 10000,
                                        "allow_votes": True,
                                        "allow_curation_rewards": True,
                                    }

            :param str reply_identifier: Identifier of the post to reply to. Takes the
                                         form ``@author/permlink``
            :param str category: (deprecated, see ``tags``) Allows to
                define a category for new posts.  It is highly recommended
                to provide a category as posts end up in ``spam`` otherwise.
                If no category is provided but ``tags``, then the first tag
                will be used as category
            :param array tags: The tags to flag the post with. If no
                category is used, then the first tag will be used as
                category
        """

        if not author and config["default_author"]:
            author = config["default_author"]

        if not author:
            raise ValueError(
                "Please define an author. (Try 'piston set default_author'"
            )

        # Deal with meta data
        if not isinstance(meta, dict):
            try:
                meta = json.loads(meta)
            except:
                meta = {}

        # Default "app"
        if "app" not in meta:
            version = pkg_resources.require("piston-lib")[0].version
            meta["app"] = "pysteem/{}".format(version)

        # Identify the comment options
        options = {}
        if "max_accepted_payout" in meta:
            options["max_accepted_payout"] = meta.pop("max_accepted_payout", None)
        if "percent_steem_dollars" in meta:
            options["percent_steem_dollars"] = meta.pop("percent_steem_dollars", None)
        if "allow_votes" in meta:
            options["allow_votes"] = meta.pop("allow_votes", None)
        if "allow_curation_rewards" in meta:
            options["allow_curation_rewards"] = meta.pop("allow_curation_rewards", None)
        if "extensions" in meta:
            options["extensions"] = meta.pop("extensions", [])

        # deal with the category and tags
        if isinstance(tags, str):
            tags = list(filter(None, (re.split("[\W_]", tags))))
        if not category and tags:
            # extract the first tag
            category = tags[0]
            tags = list(set(tags))
            # do not use the first tag in tags
            meta.update({"tags": tags[1:]})
        elif tags:
            # store everything in tags
            tags = list(set(tags))
            meta.update({"tags": tags})

        # Deal with replies
        if reply_identifier and not category:
            parent_author, parent_permlink = resolveIdentifier(reply_identifier)
            if not permlink:
                permlink = derivePermlink(title, parent_permlink)
        elif category and not reply_identifier:
            parent_permlink = derivePermlink(category)
            parent_author = ""
            if not permlink:
                permlink = derivePermlink(title)
        elif not category and not reply_identifier:
            parent_author = ""
            parent_permlink = ""
            if not permlink:
                permlink = derivePermlink(title)
        else:
            raise ValueError(
                "You can't provide a category while replying to a post"
            )

        postOp = operations.Comment(
            **{"parent_author": parent_author,
               "parent_permlink": parent_permlink,
               "author": author,
               "permlink": permlink,
               "title": title,
               "body": body,
               "json_metadata": meta}
        )
        op = [postOp]

        # If comment_options are used, add a new op to the transaction
        if options:
            default_max_payout = "1000000.000 %s" % self.symbol("SBD")
            op.append(
                operations.Comment_options(**{
                    "author": author,
                    "permlink": permlink,
                    "max_accepted_payout": options.get("max_accepted_payout", default_max_payout),
                    "percent_steem_dollars": int(
                        options.get("percent_steem_dollars", 100) * STEEMIT_1_PERCENT
                    ),
                    "allow_votes": options.get("allow_votes", True),
                    "allow_curation_rewards": options.get("allow_curation_rewards", True),
                    "extensions": options.get("extensions", [])}))

        return self.finalizeOp(op, author, "posting")

    def vote(self,
             identifier,
             weight,
             voter=None):
        """ Vote for a post

            :param str identifier: Identifier for the post to upvote Takes
                                   the form ``@author/permlink``
            :param float weight: Voting weight. Range: -100.0 - +100.0. May
                                 not be 0.0
            :param str voter: Voter to use for voting. (Optional)

            If ``voter`` is not defines, the ``default_voter`` will be taken or
            a ValueError will be raised

            .. code-block:: python

                piston set default_voter <account>
        """
        if not voter:
            if "default_voter" in config:
                voter = config["default_voter"]
        if not voter:
            raise ValueError("You need to provide a voter account")

        post_author, post_permlink = resolveIdentifier(identifier)

        op = operations.Vote(
            **{"voter": voter,
               "author": post_author,
               "permlink": post_permlink,
               "weight": int(weight * STEEMIT_1_PERCENT)}
        )

        return self.finalizeOp(op, voter, "posting")

    def create_account(self,
                       account_name,
                       json_meta={},
                       creator=None,
                       owner_key=None,
                       active_key=None,
                       posting_key=None,
                       memo_key=None,
                       password=None,
                       fee=None,
                       delegation='0.000000 VESTS',
                       additional_owner_keys=[],
                       additional_active_keys=[],
                       additional_posting_keys=[],
                       additional_owner_accounts=[],
                       additional_active_accounts=[],
                       additional_posting_accounts=[],
                       storekeys=True,
                       ):
        """ Create new account in Steem

            The brainkey/password can be used to recover all generated keys (see
            `pistonbase.account` for more details.

            By default, this call will use ``default_author`` to
            register a new name ``account_name`` with all keys being
            derived from a new brain key that will be returned. The
            corresponding keys will automatically be installed in the
            wallet.

            .. note:: Account creations cost a fee that is defined by
                       the network. If you create an account, you will
                       need to pay for that fee!

            .. warning:: Don't call this method unless you know what
                          you are doing! Be sure to understand what this
                          method does and where to find the private keys
                          for your account.

            .. note:: Please note that this imports private keys
                      (if password is present) into the wallet by
                      default. However, it **does not import the owner
                      key** for security reasons. Do NOT expect to be
                      able to recover it from the wallet if you lose
                      your password!

            :param str account_name: (**required**) new account name
            :param str json_meta: Optional meta data for the account
            :param str creator: which account should pay the registration fee
                                (defaults to ``default_author``)
            :param str owner_key: Main owner key
            :param str active_key: Main active key
            :param str posting_key: Main posting key
            :param str memo_key: Main memo_key
            :param str password: Alternatively to providing keys, one
                                 can provide a password from which the
                                 keys will be derived
            :param array additional_owner_keys:  Additional owner public keys
            :param array additional_active_keys: Additional active public keys
            :param array additional_posting_keys: Additional posting public keys
            :param array additional_owner_accounts: Additional owner account names
            :param array additional_active_accounts: Additional acctive account names
            :param array additional_posting_accounts: Additional posting account names
            :param bool storekeys: Store new keys in the wallet (default: ``True``)
            :raises AccountExistsException: if the account already exists on the blockchain

        """
        assert len(account_name) <= 16, "Account name must be at most 16 chars long"

        if not creator and config["default_author"]:
            creator = config["default_author"]
        if not creator:
            raise ValueError(
                "Not creator account given. Define it with " +
                "creator=x, or set the default_author using piston")
        if password and (owner_key or posting_key or active_key or memo_key):
            raise ValueError(
                "You cannot use 'password' AND provide keys!"
            )

        account = None
        try:
            account = Account(account_name, steem_instance=self)
        except:
            pass
        if account:
            raise AccountExistsException

        " Generate new keys from password"
        from pistonbase.account import PasswordKey, PublicKey
        if password:
            posting_key = PasswordKey(account_name, password, role="posting")
            active_key = PasswordKey(account_name, password, role="active")
            owner_key = PasswordKey(account_name, password, role="owner")
            memo_key = PasswordKey(account_name, password, role="memo")
            posting_pubkey = posting_key.get_public_key()
            active_pubkey = active_key.get_public_key()
            owner_pubkey = owner_key.get_public_key()
            memo_pubkey = memo_key.get_public_key()
            posting_privkey = posting_key.get_private_key()
            active_privkey = active_key.get_private_key()
            # owner_privkey   = owner_key.get_private_key()
            memo_privkey = memo_key.get_private_key()
            # store private keys
            if storekeys:
                # self.wallet.addPrivateKey(owner_privkey)
                self.wallet.addPrivateKey(active_privkey)
                self.wallet.addPrivateKey(posting_privkey)
                self.wallet.addPrivateKey(memo_privkey)
        elif (owner_key and posting_key and active_key and memo_key):
            posting_pubkey = PublicKey(posting_key, prefix=self.rpc.chain_params["prefix"])
            active_pubkey = PublicKey(active_key, prefix=self.rpc.chain_params["prefix"])
            owner_pubkey = PublicKey(owner_key, prefix=self.rpc.chain_params["prefix"])
            memo_pubkey = PublicKey(memo_key, prefix=self.rpc.chain_params["prefix"])
        else:
            raise ValueError(
                "Call incomplete! Provide either a password or public keys!"
            )

        owner = format(owner_pubkey, self.rpc.chain_params["prefix"])
        active = format(active_pubkey, self.rpc.chain_params["prefix"])
        posting = format(posting_pubkey, self.rpc.chain_params["prefix"])
        memo = format(memo_pubkey, self.rpc.chain_params["prefix"])

        owner_key_authority = [[owner, 1]]
        active_key_authority = [[active, 1]]
        posting_key_authority = [[posting, 1]]
        owner_accounts_authority = []
        active_accounts_authority = []
        posting_accounts_authority = []

        # additional authorities
        for k in additional_owner_keys:
            owner_key_authority.append([k, 1])
        for k in additional_active_keys:
            active_key_authority.append([k, 1])
        for k in additional_posting_keys:
            posting_key_authority.append([k, 1])

        for k in additional_owner_accounts:
            owner_accounts_authority.append([k, 1])
        for k in additional_active_accounts:
            active_accounts_authority.append([k, 1])
        for k in additional_posting_accounts:
            posting_accounts_authority.append([k, 1])

        props = self.rpc.get_chain_properties()
        # the Account_create operation expects a string
        # so this is a little hacky, but it's the easiest way to deal
        # with STEEM/Graphene amounts.
        # HF18 requires the fee to be multiplied by 30
        if fee is None:
            f = Amount(props["account_creation_fee"])
            fee = str(Amount('{} STEEM'.format(f.amount * 30)))
        s = {'creator': creator,
             'fee': fee,
             'json_metadata': json_meta,
             'memo_key': memo,
             'new_account_name': account_name,
             'owner': {'account_auths': owner_accounts_authority,
                       'key_auths': owner_key_authority,
                       'weight_threshold': 1},
             'active': {'account_auths': active_accounts_authority,
                        'key_auths': active_key_authority,
                        'weight_threshold': 1},
             'posting': {'account_auths': posting_accounts_authority,
                         'key_auths': posting_key_authority,
                         'weight_threshold': 1},
             'prefix': self.rpc.chain_params["prefix"],
             'delegation': delegation}

        op = operations.Account_create_with_delegation(**s)

        return self.finalizeOp(op, creator, "active")

    def transfer(self, to, amount, asset, memo="", account=None):
        """ Transfer SBD or STEEM to another account.

            :param str to: Recipient
            :param float amount: Amount to transfer
            :param str asset: Asset to transfer (``SBD`` or ``STEEM``)
            :param str memo: (optional) Memo, may begin with `#` for encrypted messaging
            :param str account: (optional) the source account for the transfer if not ``default_account``
        """
        if not account:
            if "default_account" in config:
                account = config["default_account"]
        if not account:
            raise ValueError("You need to provide an account")

        assert asset == self.symbol("SBD") or asset == self.symbol("steem")

        if memo and memo[0] == "#":
            from pistonbase import memo as Memo
            memo_wif = self.wallet.getMemoKeyForAccount(account)
            if not memo_wif:
                raise MissingKeyError("Memo key for %s missing!" % account)
            to_account = Account(to, steem_instance=self)
            nonce = str(random.getrandbits(64))
            memo = Memo.encode_memo(
                PrivateKey(memo_wif),
                PublicKey(to_account["memo_key"], prefix=self.rpc.chain_params["prefix"]),
                nonce,
                memo,
                prefix=self.rpc.chain_params["prefix"]
            )

        op = operations.Transfer(
            **{"from": account,
               "to": to,
               "amount": '{:.{prec}f} {asset}'.format(
                   float(amount),
                   prec=3,
                   asset=asset
               ),
               "memo": memo
               }
        )
        return self.finalizeOp(op, account, "active")

    def withdraw_vesting(self, amount, account=None):
        """ Withdraw VESTS from the vesting account.

            :param float amount: number of VESTS to withdraw over a period of 104 weeks
            :param str account: (optional) the source account for the transfer if not ``default_account``
        """
        if not account:
            if "default_account" in config:
                account = config["default_account"]
        if not account:
            raise ValueError("You need to provide an account")

        op = operations.Withdraw_vesting(
            **{"account": account,
               "vesting_shares": '{:.{prec}f} {asset}'.format(
                   float(amount),
                   prec=6,
                   asset="VESTS"
               ),
               }
        )

        return self.finalizeOp(op, account, "active")

    def transfer_to_vesting(self, amount, to=None, account=None):
        """ Vest STEEM

            :param float amount: number of STEEM to vest
            :param str to: (optional) the source account for the transfer if not ``default_account``
            :param str account: (optional) the source account for the transfer if not ``default_account``
        """
        if not account:
            if "default_account" in config:
                account = config["default_account"]
        if not account:
            raise ValueError("You need to provide an account")

        if not to:
            to = account  # powerup on the same account

        op = operations.Transfer_to_vesting(
            **{"from": account,
               "to": to,
               "amount": '{:.{prec}f} {asset}'.format(
                   float(amount),
                   prec=3,
                   asset=self.symbol("steem"))
               }
        )

        return self.finalizeOp(op, account, "active")

    def convert(self, amount, account=None, requestid=None):
        """ Convert SteemDollars to Steem (takes one week to settle)

            :param float amount: number of VESTS to withdraw over a period of 104 weeks
            :param str account: (optional) the source account for the transfer if not ``default_account``
            :param str requestid: (optional) identifier for tracking the conversion`
        """
        if not account and "default_account" in config:
            account = config["default_account"]
        if not account:
            raise ValueError("You need to provide an account")

        if requestid:
            requestid = int(requestid)
        else:
            requestid = random.getrandbits(32)
        op = operations.Convert(
            **{"owner": account,
               "requestid": requestid,
               "amount": '{:.{prec}f} {asset}'.format(
                   float(amount),
                   prec=3,
                   asset=self.symbol("SBD")
               )}
        )

        return self.finalizeOp(op, account, "active")

    def transfer_to_savings(self, amount, currency, memo, to=None, account=None):
        """ Transfer SBD or STEEM into a 'savings' account.

            :param float amount: STEEM or SBD amount
            :param float currency: 'STEEM' or 'SBD'
            :param str memo: (optional) Memo
            :param str to: (optional) the source account for the transfer if not ``default_account``
            :param str account: (optional) the source account for the transfer if not ``default_account``
        """
        self._valid_currency(currency)

        if not account:
            if "default_account" in config:
                account = config["default_account"]
        if not account:
            raise ValueError("You need to provide an account")

        if not to:
            to = account  # move to savings on same account

        op = operations.Transfer_to_savings(
            **{
                "from": account,
                "to": to,
                "amount": '{:.{prec}f} {asset}'.format(
                    float(amount),
                    prec=3,
                    asset=currency),
                "memo": memo,
            }
        )
        return self.finalizeOp(op, account, "active")

    def transfer_from_savings(self, amount, currency, memo, request_id=None, to=None, account=None):
        """ Withdraw SBD or STEEM from 'savings' account.

            :param float amount: STEEM or SBD amount
            :param float currency: 'STEEM' or 'SBD'
            :param str memo: (optional) Memo
            :param str request_id: (optional) identifier for tracking or cancelling the withdrawal
            :param str to: (optional) the source account for the transfer if not ``default_account``
            :param str account: (optional) the source account for the transfer if not ``default_account``
        """
        self._valid_currency(currency)

        if not account:
            if "default_account" in config:
                account = config["default_account"]
        if not account:
            raise ValueError("You need to provide an account")

        if not to:
            to = account  # move to savings on same account

        if request_id:
            request_id = int(request_id)
        else:
            request_id = random.getrandbits(32)

        op = operations.Transfer_from_savings(
            **{
                "from": account,
                "request_id": request_id,
                "to": to,
                "amount": '{:.{prec}f} {asset}'.format(
                    float(amount),
                    prec=3,
                    asset=currency),
                "memo": memo,
            }
        )
        return self.finalizeOp(op, account, "active")

    def transfer_from_savings_cancel(self, request_id, account=None):
        """ Cancel a withdrawal from 'savings' account.

            :param str request_id: Identifier for tracking or cancelling the withdrawal
            :param str account: (optional) the source account for the transfer if not ``default_account``
        """
        if not account:
            if "default_account" in config:
                account = config["default_account"]
        if not account:
            raise ValueError("You need to provide an account")

        op = operations.Cancel_transfer_from_savings(
            **{
                "from": account,
                "request_id": request_id,
            }
        )
        return self.finalizeOp(op, account, "active")

    def witness_feed_publish(self, steem_usd_price, quote="1.000", account=None):
        """ Publish a feed price as a witness.

            :param float steem_usd_price: Price of STEEM in USD (implied price)
            :param float quote: (optional) Quote Price. Should be 1.000, unless we are adjusting the feed to support the peg.
            :param str account: (optional) the source account for the transfer if not ``default_account``
        """
        if not account:
            if "default_account" in config:
                account = config["default_account"]
        if not account:
            raise ValueError("You need to provide an account")

        op = operations.Feed_publish(
            **{
                "publisher": account,
                "exchange_rate": {
                    "base": "%s %s" % (steem_usd_price, self.symbol("SBD")),
                    "quote": "%s %s" % (quote, self.symbol("steem")),
                }
            }
        )
        return self.finalizeOp(op, account, "active")

    def witness_update(self, signing_key, url, props, account=None):
        """ Update witness

            :param pubkey signing_key: Signing key
            :param str url: URL
            :param dict props: Properties
            :param str account: (optional) witness account name

             Properties:::

                {
                    "account_creation_fee": x,
                    "maximum_block_size": x,
                    "sbd_interest_rate": x,
                }

        """
        if not account:
            if "default_account" in config:
                account = config["default_account"]
        if not account:
            raise ValueError("You need to provide an account")

        try:
            PublicKey(signing_key)
        except Exception as e:
            raise e

        op = operations.Witness_update(
            **{
                "owner": account,
                "url": url,
                "block_signing_key": signing_key,
                "props": props,
                "fee": "0.000 %s" % self.symbol("steem"),
                "prefix": self.rpc.chain_params["prefix"]
            }
        )
        return self.finalizeOp(op, account, "active")

    @staticmethod
    def _valid_currency(currency):
        if currency not in [
            Steem.rpc.chain_params["sbd_symbol"],
            Steem.rpc.chain_params["steem_symbol"]
        ]:
            raise TypeError("Unsupported currency %s" % currency)

    def get_content(self, identifier):
        """ Get the full content of a post.

            :param str identifier: Identifier for the post to upvote Takes
                                   the form ``@author/permlink``
        """
        return Post(identifier, steem_instance=self)

    def get_post(self, identifier):
        """ Get the full content of a post.

            :param str identifier: Identifier for the post to upvote Takes
                                   the form ``@author/permlink``
        """
        return Post(identifier, steem_instance=self)

    def get_recommended(self, user):
        """ (obsolete) Get recommended posts for user
        """
        log.critical("get_recommended has been removed from the backend.")
        return []

    def get_blog(self, user):
        """ Get blog posts of a user

            :param str user: Show recommendations for this author
        """
        from .blog import Blog
        return Blog(user)

    def get_replies(self, author, skipown=True):
        """ Get replies for an author

            :param str author: Show replies for this author
            :param bool skipown: Do not show my own replies
        """
        state = self.rpc.get_state("/@%s/recent-replies" % author)
        replies = state["accounts"][author].get("recent_replies", [])
        discussions = []
        for reply in replies:
            post = state["content"][reply]
            if skipown and post["author"] == author:
                continue
            discussions.append(Post(post, steem_instance=self))
        return discussions

    def get_promoted(self):
        """ Get promoted posts
        """
        state = self.rpc.get_state("/promoted")
        # why is there a empty key in the struct?
        promoted = state["discussion_idx"][''].get("promoted", [])
        r = []
        for p in promoted:
            post = state["content"].get(p)
            r.append(Post(post, steem_instance=self))
        return r

    def get_posts(self, limit=10,
                  sort="hot",
                  category=None,
                  start=None):
        """ Get multiple posts in an array.

            :param int limit: Limit the list of posts by ``limit``
            :param str sort: Sort the list by "recent" or "payout"
            :param str category: Only show posts in this category
            :param str start: Show posts after this post. Takes an
                              identifier of the form ``@author/permlink``
        """

        discussion_query = {"tag": category,
                            "limit": limit,
                            }
        if start:
            author, permlink = resolveIdentifier(start)
            discussion_query["start_author"] = author
            discussion_query["start_permlink"] = permlink

        if sort not in ["trending", "created", "active", "cashout",
                        "payout", "votes", "children", "hot"]:
            raise Exception("Invalid choice of '--sort'!")

        func = getattr(self.rpc, "get_discussions_by_%s" % sort)
        r = []
        for p in func(discussion_query):
            r.append(Post(p, steem_instance=self))
        return r

    def get_comments(self, identifier):
        """ Return **first-level** comments of a post.

            :param str identifier: Identifier of a post. Takes an
                                   identifier of the form ``@author/permlink``
        """
        return Post(identifier, steem_instance=self).get_comments()

    def get_categories(self, sort="trending", begin=None, limit=10):
        """ List categories

            :param str sort: Sort categories by "trending", "best",
                             "active", or "recent"
            :param str begin: Show categories after this
                              identifier of the form ``@author/permlink``
            :param int limit: Limit categories by ``x``
        """
        if sort == "trending":
            func = self.rpc.get_trending_categories
        elif sort == "best":
            func = self.rpc.get_best_categories
        elif sort == "active":
            func = self.rpc.get_active_categories
        elif sort == "recent":
            func = self.rpc.get_recent_categories
        else:
            log.error("Invalid choice of '--sort' (%s)!" % sort)
            return

        return func(begin, limit)

    def get_balances(self, account=None):
        """ Get the balance of an account

            :param str account: (optional) the source account for the transfer if not ``default_account``
        """
        if not account:
            if "default_account" in config:
                account = config["default_account"]
        if not account:
            raise ValueError("You need to provide an account")
        a = Account(account, steem_instance=self)
        info = self.rpc.get_dynamic_global_properties()
        steem_per_mvest = (
            Amount(info["total_vesting_fund_steem"]).amount /
            (Amount(info["total_vesting_shares"]).amount / 1e6)
        )
        vesting_shares = Amount(a["vesting_shares"])
        vesting_shares_steem = Amount("%f %s" % (
            float(vesting_shares) / 1e6 * steem_per_mvest,
            "STEEM"
        ))

        return {
            "balance": Amount(a["balance"]),
            "vesting_shares": vesting_shares,
            "sbd_balance": Amount(a["sbd_balance"]),
            "savings_balance": Amount(a["savings_balance"]),
            "savings_sbd_balance": Amount(a["savings_sbd_balance"]),
            # computed amounts
            "vesting_shares_steem": Amount(vesting_shares_steem),
        }

    def get_account_history(self, account, **kwargs):
        return Account(account, steem_instance=self).rawhistory(**kwargs)

    def decode_memo(self, enc_memo, account):
        """ Try to decode an encrypted memo
        """
        assert enc_memo[0] == "#", "decode memo requires memos to start with '#'"
        keys = memo.involved_keys(enc_memo)
        wif = None
        for key in keys:
            wif = self.wallet.getPrivateKeyForPublicKey(str(key))
            if wif:
                break
        if not wif:
            raise MissingKeyError
        return memo.decode_memo(PrivateKey(wif), enc_memo)

    def stream_comments(self, *args, **kwargs):
        """ Generator that yields posts when they come in

            To be used in a for loop that returns an instance of `Post()`.
        """
        for c in Blockchain(
            mode=kwargs.get("mode", "irreversible"),
            steem_instance=self,
        ).stream("comment", *args, **kwargs):
            yield Post(c, steem_instance=self)

    def interest(self, account):
        """ Caluclate interest for an account

            :param str account: Account name to get interest for
        """
        account = Account(account, steem_instance=self)
        last_payment = formatTimeString(account["sbd_last_interest_payment"])
        next_payment = last_payment + timedelta(days=30)
        interest_rate = self.info()["sbd_interest_rate"] / 100  # the result is in percent!
        interest_amount = (interest_rate / 100) * int(
            int(account["sbd_seconds"]) / (60 * 60 * 24 * 356)
        ) * 10 ** -3

        return {
            "interest": interest_amount,
            "last_payment": last_payment,
            "next_payment": next_payment,
            "next_payment_duration": next_payment - datetime.now(),
            "interest_rate": interest_rate,
        }

    def set_withdraw_vesting_route(self, to, percentage=100,
                                   account=None, auto_vest=False):
        """ Set up a vesting withdraw route. When vesting shares are
            withdrawn, they will be routed to these accounts based on the
            specified weights.

            :param str to: Recipient of the vesting withdrawal
            :param float percentage: The percent of the withdraw to go
                to the 'to' account.
            :param str account: (optional) the vesting account
            :param bool auto_vest: Set to true if the from account
                should receive the VESTS as VESTS, or false if it should
                receive them as STEEM. (defaults to ``False``)
        """
        if not account:
            if "default_account" in config:
                account = config["default_account"]
        if not account:
            raise ValueError("You need to provide an account")

        op = operations.Set_withdraw_vesting_route(
            **{"from_account": account,
               "to_account": to,
               "percent": int(percentage * STEEMIT_1_PERCENT),
               "auto_vest": auto_vest
               }
        )

        return self.finalizeOp(op, account, "active")

    def _test_weights_treshold(self, authority):
        weights = 0
        for a in authority["account_auths"]:
            weights += a[1]
        for a in authority["key_auths"]:
            weights += a[1]
        if authority["weight_threshold"] > weights:
            raise ValueError("Threshold too restrictive!")

    def allow(self, foreign, weight=None, permission="posting",
              account=None, threshold=None):
        """ Give additional access to an account by some other public
            key or account.

            :param str foreign: The foreign account that will obtain access
            :param int weight: (optional) The weight to use. If not
                define, the threshold will be used. If the weight is
                smaller than the threshold, additional signatures will
                be required. (defaults to threshold)
            :param str permission: (optional) The actual permission to
                modify (defaults to ``posting``)
            :param str account: (optional) the account to allow access
                to (defaults to ``default_author``)
            :param int threshold: The threshold that needs to be reached
                by signatures to be able to interact
        """
        if not account:
            if "default_author" in config:
                account = config["default_author"]
        if not account:
            raise ValueError("You need to provide an account")

        if permission not in ["owner", "posting", "active"]:
            raise ValueError(
                "Permission needs to be either 'owner', 'posting', or 'active"
            )
        account = Account(account, steem_instance=self)
        if not weight:
            weight = account[permission]["weight_threshold"]

        authority = account[permission]
        try:
            pubkey = PublicKey(foreign)
            authority["key_auths"].append([
                str(pubkey),
                weight
            ])
        except:
            try:
                foreign_account = Account(foreign, steem_instance=self)
                authority["account_auths"].append([
                    foreign_account["name"],
                    weight
                ])
            except:
                raise ValueError(
                    "Unknown foreign account or unvalid public key"
                )
        if threshold:
            authority["weight_threshold"] = threshold
            self._test_weights_treshold(authority)

        op = operations.Account_update(
            **{"account": account["name"],
               permission: authority,
               "memo_key": account["memo_key"],
               "json_metadata": account["json_metadata"],
               'prefix': self.rpc.chain_params["prefix"]}
        )
        if permission == "owner":
            return self.finalizeOp(op, account["name"], "owner")
        else:
            return self.finalizeOp(op, account["name"], "active")

    def disallow(self, foreign, permission="posting",
                 account=None, threshold=None):
        """ Remove additional access to an account by some other public
            key or account.

            :param str foreign: The foreign account that will obtain access
            :param str permission: (optional) The actual permission to
                modify (defaults to ``posting``)
            :param str account: (optional) the account to allow access
                to (defaults to ``default_author``)
            :param int threshold: The threshold that needs to be reached
                by signatures to be able to interact
        """
        if not account:
            if "default_author" in config:
                account = config["default_author"]
        if not account:
            raise ValueError("You need to provide an account")

        if permission not in ["owner", "posting", "active"]:
            raise ValueError(
                "Permission needs to be either 'owner', 'posting', or 'active"
            )
        account = Account(account, steem_instance=self)
        authority = account[permission]

        try:
            pubkey = PublicKey(foreign, prefix=self.rpc.chain_params["prefix"])
            affected_items = list(
                filter(lambda x: x[0] == str(pubkey),
                       authority["key_auths"]))
            authority["key_auths"] = list(filter(
                lambda x: x[0] != str(pubkey),
                authority["key_auths"]
            ))
        except:
            try:
                foreign_account = Account(foreign, steem_instance=self)
                affected_items = list(
                    filter(lambda x: x[0] == foreign_account["name"],
                           authority["account_auths"]))
                authority["account_auths"] = list(filter(
                    lambda x: x[0] != foreign_account["name"],
                    authority["account_auths"]
                ))
            except:
                raise ValueError(
                    "Unknown foreign account or unvalid public key"
                )

        removed_weight = affected_items[0][1]

        # Define threshold
        if threshold:
            authority["weight_threshold"] = threshold

        # Correct threshold (at most by the amount removed from the
        # authority)
        try:
            self._test_weights_treshold(authority)
        except:
            log.critical(
                "The account's threshold will be reduced by %d"
                % (removed_weight)
            )
            authority["weight_threshold"] -= removed_weight
            self._test_weights_treshold(authority)

        op = operations.Account_update(
            **{"account": account["name"],
               permission: authority,
               "memo_key": account["memo_key"],
               "json_metadata": account["json_metadata"]}
        )
        if permission == "owner":
            return self.finalizeOp(op, account["name"], "owner")
        else:
            return self.finalizeOp(op, account["name"], "active")

    def update_memo_key(self, key, account=None):
        """ Update an account's memo public key

            This method does **not** add any private keys to your
            wallet but merely changes the memo public key.

            :param str key: New memo public key
            :param str account: (optional) the account to allow access
                to (defaults to ``default_author``)
        """
        if not account:
            if "default_author" in config:
                account = config["default_author"]
        if not account:
            raise ValueError("You need to provide an account")

        PublicKey(key)  # raises exception if invalid
        account = Account(account, steem_instance=self)
        op = operations.Account_update(
            **{"account": account["name"],
               "memo_key": key,
               "json_metadata": account["json_metadata"]}
        )
        return self.finalizeOp(op, account["name"], "active")

    def approve_witness(self, witness, account=None, approve=True):
        """ Vote **for** a witness. This method adds a witness to your
            set of approved witnesses. To remove witnesses see
            ``disapprove_witness``.

            :param str witness: witness to approve
            :param str account: (optional) the account to allow access
                to (defaults to ``default_author``)
        """
        if not account:
            if "default_author" in config:
                account = config["default_author"]
        if not account:
            raise ValueError("You need to provide an account")
        account = Account(account, steem_instance=self)
        op = operations.Account_witness_vote(
            **{"account": account["name"],
               "witness": witness,
               "approve": approve,
               })
        return self.finalizeOp(op, account["name"], "active")

    def disapprove_witness(self, witness, account=None, approve=True):
        """ Remove vote for a witness. This method removes
            a witness from your set of approved witnesses. To add
            witnesses see ``approve_witness``.

            :param str witness: witness to approve
            :param str account: (optional) the account to allow access
                to (defaults to ``default_author``)
        """
        return self.approve_witness(witness=witness, account=account, approve=False)

    def custom_json(self, id, json, required_auths=[], required_posting_auths=[]):
        """ Create a custom json operation

            :param str id: identifier for the custom json (max length 32 bytes)
            :param json json: the json data to put into the custom_json operation
            :param list required_auths: (optional) required auths
            :param list required_posting_auths: (optional) posting auths
        """
        account = None
        if len(required_auths):
            account = required_auths[0]
        elif len(required_posting_auths):
            account = required_posting_auths[0]
        else:
            raise Exception("At least on account needs to be specified")
        op = operations.Custom_json(
            **{"json": json,
               "required_auths": required_auths,
               "required_posting_auths": required_posting_auths,
               "id": id})
        return self.finalizeOp(op, account, "posting")

    def resteem(self, identifier, account=None):
        """ Resteem a post

            :param str identifier: post identifier (@<account>/<permlink>)
            :param str account: (optional) the account to allow access
                to (defaults to ``default_author``)
        """
        if not account:
            if "default_author" in config:
                account = config["default_author"]
        if not account:
            raise ValueError("You need to provide an account")
        author, permlink = resolveIdentifier(identifier)
        return self.custom_json(
            id="follow",
            json=["reblog",
                  {"account": account,
                   "author": author,
                   "permlink": permlink
                   }],
            required_posting_auths=[account]
        )

    def unfollow(self, unfollow, what=["blog"], account=None):
        """ Unfollow another account's blog

            :param str unfollow: Follow this account
            :param list what: List of states to follow (defaults to ``['blog']``)
            :param str account: (optional) the account to allow access
                to (defaults to ``default_account``)
        """
        # FIXME: removing 'blog' from the array requires to first read
        # the follow.what from the blockchain
        return self.follow(unfollow, what=[], account=account)

    def follow(self, follow, what=["blog"], account=None):
        """ Follow another account's blog

            :param str follow: Follow this account
            :param list what: List of states to follow (defaults to ``['blog']``)
            :param str account: (optional) the account to allow access
                to (defaults to ``default_account``)
        """
        if not account:
            if "default_account" in config:
                account = config["default_account"]
        if not account:
            raise ValueError("You need to provide an account")
        return self.custom_json(
            id="follow",
            json=['follow', {
                'follower': account,
                'following': follow,
                'what': what}],
            required_posting_auths=[account]
        )

    def reblog(self, *args, **kwargs):
        """ See resteem() """
        self.resteem(*args, **kwargs)

    def update_account_profile(self, profile, account=None):
        """ Update an account's meta data (json_meta)

            :param dict json: The meta data to use (i.e. use Profile() from account.py)
            :param str account: (optional) the account to allow access
                to (defaults to ``default_account``)
        """
        if not account:
            if "default_author" in config:
                account = config["default_account"]
        if not account:
            raise ValueError("You need to provide an account")
        account = Account(account, steem_instance=self)
        op = operations.Account_update(
            **{"account": account["name"],
               "memo_key": account["memo_key"],
               "json_metadata": profile}
        )
        return self.finalizeOp(op, account["name"], "active")

    def comment_options(self, identifier, options, account=None):
        """ Set the comment options

            :param str identifier: Post identifier
            :param dict options: The options to define.
            :param str account: (optional) the account to allow access
                to (defaults to ``default_account``)

            For the options, you have these defaults:::

                    {
                        "author": "",
                        "permlink": "",
                        "max_accepted_payout": "1000000.000 SBD",
                        "percent_steem_dollars": 10000,
                        "allow_votes": True,
                        "allow_curation_rewards": True,
                    }

        """
        if not account:
            if "default_author" in config:
                account = config["default_account"]
        if not account:
            raise ValueError("You need to provide an account")
        account = Account(account, steem_instance=self)
        author, permlink = resolveIdentifier(identifier)
        default_max_payout = "1000000.000 %s" % self.symbol("SBD")
        op = operations.Comment_options(
            **{
                "author": author,
                "permlink": permlink,
                "max_accepted_payout": options.get("max_accepted_payout", default_max_payout),
                "percent_steem_dollars": options.get("percent_steem_dollars", 100) * STEEMIT_1_PERCENT,
                "allow_votes": options.get("allow_votes", True),
                "allow_curation_rewards": options.get("allow_curation_rewards", True),
            }
        )
        return self.finalizeOp(op, account["name"], "posting")
