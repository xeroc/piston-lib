import asyncio
from steemapi.steemasyncclient import SteemAsyncClient, Config

import aiohttp
import re
import dateutil.parser
from pprint import pprint


account = "witness-account"  # Replace with  account you wish to monitor

re_asset = re.compile(r'(?P<number>\d*\.?\d+)\s?(?P<unit>[a-zA-Z]+)')

def read_asset(asset_string):
   res = re_asset.match(asset_string)
   return {'value': float(res.group('number')), 'symbol': res.group('unit')}


def read_time(time_string):
   return int( dateutil.parser.parse(time_string + "UTC").timestamp() )
      
@asyncio.coroutine
def get_steem_price(sess):
      response = yield from sess.get("https://coinmarketcap-nexuist.rhcloud.com/api/steem")
      ret = yield from response.json()
      return ret["price"]["usd"]

@asyncio.coroutine
def get_witness_price_feed(steem, acct):
      r = yield from steem.wallet.get_witness(acct)
      last_update_time = read_time(r["last_sbd_exchange_update"])
      p = r["sbd_exchange_rate"]
      last_price = read_asset(p["base"])["value"] / read_asset(p["quote"])["value"]
      return (last_update_time, last_price)

@asyncio.coroutine
def start(steem):
   with aiohttp.ClientSession() as session:
      futures = {"time": None, "exchange_price": None, "witness_price": None, "db": None}
      last_witness_update_time, last_witness_price = yield from get_witness_price_feed(steem, account)
      r = yield from steem.db.get_dynamic_global_properties()
      last_time = read_time(r["time"])
      cur_time = last_time
      first_time = True
      steem_price = yield from get_steem_price(session)
      futures["time"] = asyncio.async(asyncio.sleep(0))
      needs_updating = False
      while True:
         ftrs = []
         for f in futures.values():
            if f != None:
               ftrs.append(f)
         done, pending = yield from asyncio.wait(ftrs, return_when=asyncio.FIRST_COMPLETED)
        
         old_futures = {}
         for k, f in futures.items():
            old_futures[k] = futures[k]
         for k, f in old_futures.items():
            if f in done:
               futures[k] = None
               if k == "time":
                  futures["time"] = asyncio.async(asyncio.sleep(3))
                  if futures["db"] != None:
                     futures["db"].cancel()
                  futures["db"]   = yield from steem.db.get_dynamic_global_properties(future=True)
               elif k == "exchange_price":
                  steem_price = f.result()
                  if abs(1 - last_witness_price/steem_price) > 0.03 and (cur_time - last_witness_update_time) > 60*60:
                     if not needs_updating:
                        needs_updating = True
                        print("Price feed needs to be updated due to change in price.")
                        print("Current witness price: {} $/STEEM   Current exchange price: {} $/STEEM".format(last_witness_price, steem_price))
                  else:
                     if needs_updating and cur_time - last_witness_update_time < 24*60*60:
                        needs_updating = False
                        print("Price feed no longer needs to be updated")

               elif k == "witness_price":
                  new_last_witness_update_time, new_last_witness_price = f.result()
                  if new_last_witness_update_time != last_witness_update_time:
                     last_witness_update_time = new_last_witness_update_time
                     last_witness_price = new_last_witness_price
                     print("Price feed has been updated")
                     needs_updating = False
               elif k == "db":
                  r = f.result()
                  cur_time = read_time(r["time"])
                  if first_time or cur_time - last_time > 28: # seconds
                     first_time = False
                     print("Block number {} at time: {}".format(r["head_block_number"], r["time"]))
                     if needs_updating:
                        print("Price feed still needs updating to {} $/STEEM".format(steem_price))
                     futures["exchange_price"] = asyncio.async(get_steem_price(session))
                     futures["witness_price"] = asyncio.async(get_witness_price_feed(steem, account))
                     last_time = cur_time
                  if cur_time - last_witness_update_time >= 24*60*60:
                     if not needs_updating:
                        needs_updating = True
                        print("Price feed needs to be updated because it is too old.")
         old_futures = {}

if __name__ == "__main__":
   steem = SteemAsyncClient(Config(config_file="async_monitor_config.yml"))
   steem.run([start]) # If multiple coroutines were specified in the array, they would run concurrently


