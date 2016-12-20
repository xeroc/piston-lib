from steem.markets import Markets

if __name__ == "__main__":
    m = Markets()
    print("Fetching BTC/USD Price...")
    btc_usd = m.btc_usd()
    print(btc_usd)

    print("\nFetching STEEM/BTC Price...")
    steem_btc = m.steem_btc()
    print(steem_btc)

    print("\nFetching SBD/BTC Price...")
    sbd_btc = m.sbd_btc()
    print(sbd_btc)

    print("\nCalculating implied SBD/USD price...")
    print(m.sbd_usd_implied())

    print("\nCalculating implied STEEM/SBD price...")
    print(m.steem_sbd_implied())

    print("\nCalculating implied STEEM/USD price...")
    print(m.steem_usd_implied())
