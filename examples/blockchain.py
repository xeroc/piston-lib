from steem.chain import Blockchain

# parse the whole chain
for event in Blockchain().replay():
    print("Event: %s" % event['op_type'])
    print("Time: %s" % event['timestamp'])
    print("Body: %s\n" % event['op'])

# parse only payments from specific datetime until now
b = Blockchain()
history = b.replay(
    start_block=b.get_block_from_time("2016-09-01T00:00:00"),
    end_block=b.get_current_block(),
    filter_by=['transfer']
)
for event in history:
    payment = event['op']
    print("@%s sent %s to @%s" % (payment['from'], payment['amount'], payment['to']))

# Output:
# @victoriart sent 1.000 SBD to @null
# @dude sent 5.095 STEEM to @bittrex
# @devil sent 5.107 STEEM to @poloniex
# @pinoytravel sent 0.010 SBD to @null
# @aladdin sent 5.013 STEEM to @poloniex
# @mrwang sent 31.211 STEEM to @blocktrades
# @kodi sent 0.030 SBD to @steembingo
