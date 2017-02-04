import steem as stm

_shared_steem_instance = None


def shared_steem_instance():
    global _shared_steem_instance
    if not _shared_steem_instance:
        _shared_steem_instance = stm.Steem()  # todo: add piston config
    return _shared_steem_instance
