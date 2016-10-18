#!/usr/bin/env python3
import pprint
import time
import sys
import dateutil.parser
import yaml
import redis
import json

from steemapi.steemnoderpc import SteemNodeRPC

# My vars
from index_html2 import *
from flow_vars2 import *

pdays = float(sys.argv[1]) # how many days to get stats

# My config
my_config = yaml.load(open("steemapi.yml"))
log = my_config['log']
index_file = my_config['index_file']
pause = 0.33 # seconds

rpc = SteemNodeRPC('ws://node.steem.ws')
config = rpc.get_config()
block_interval = config["STEEMIT_BLOCK_INTERVAL"]
bpd = int(60 * 60 * 24 / block_interval) # blocks per day

pp = pprint.PrettyPrinter(indent=4)
pp.pprint(config)

props = rpc.get_dynamic_global_properties()
block_number = props['last_irreversible_block_num']
start_block = block_number - int(pdays * bpd)
pp.pprint(props)

last_block_time = rpc.get_block(start_block)['timestamp']
time_last_block = dateutil.parser.parse(last_block_time)
#pp.pprint(dys)

oper_list = ('vote',
            'comment',
            'delete_comment',
            'custom_json',
            'limit_order_create',
            'limit_order_cancel',
            'account_create',
            'account_update',
            'account_witness_vote')

exchanges = ('bittrex', 'poloniex', 'blocktrades', 'openledger',
                 'hitbtc-exchange', 'hitbtc-payout', 'changelly')

rdb = redis.Redis(host="localhost", port=6379)

block_head = {"block_interval": block_interval,
              "block_number": block_number,
              "last_block_time": last_block_time}

rdb.set("block_head", json.dumps(block_head))
read_head = json.loads( rdb.get("block_head").decode() )

with open('index.html', 'w') as fl:
      fl.write(html_1 % read_head )

print('Start from %s block till %s ...' % (start_block, block_number) )

for br in range(start_block, block_number + 1):
    dys = rpc.get_block(br)
    dys_ts = dys['timestamp']
    time_dys = dateutil.parser.parse(dys_ts)
    time_diff = time_dys - time_last_block
    dmin = time_diff.days*24*60 + time_diff.seconds/60
    if dmin == 0: # no div 0
        dmin = pause * 60
    txs = dys['transactions']
    
    for tx in txs:

        for operation in tx['operations']:

            if (operation[0] not in oper_list):

                if log:
                    print(br)
                    pp.pprint(tx['operations'])
                    #pp.pprint(dys)
                    #print(dys['previous'], dys['timestamp'])

                if operation[0] == 'pow2':
                    pow2_count += 1
                    pow2_block = block_count / pow2_count
                    pow2_time = time_diff / pow2_count

                if operation[0] == 'transfer':
                    trans_count += 1
                    if operation[1]["from"] not in exchanges \
                      and operation[1]["to"] == 'null':
                      trans_null += 1
                      amount = operation[1]['amount'].split()
                      to_null_sbd += float(amount[0])

                    elif operation[1]["from"] not in exchanges \
                        and operation[1]["to"] in exchanges:
                        trans2ex += 1
                        amount = operation[1]['amount'].split()
                        if amount[1] == 'SBD':
                            to_ex_sbd += float(amount[0])
                        elif amount[1] == 'STEEM':
                            to_ex_steem += float(amount[0])
                        else:
                            print('\n!!! Unknown currency !!!\n')

                    elif operation[1]["from"] in exchanges \
                        and operation[1]["to"] not in exchanges:
                        trans4ex += 1
                        amount = operation[1]['amount'].split()
                        if amount[1] == 'SBD':
                            from_ex_sbd += float(amount[0])
                        elif amount[1] == 'STEEM':
                            from_ex_steem += float(amount[0])
                        else:
                            print('\n!!! Unknown currency !!!\n')

                    elif operation[1]["from"] not in exchanges \
                        and operation[1]["to"] not in exchanges:
                        trans_u += 1

                    elif operation[1]["from"] in exchanges \
                        and operation[1]["to"] in exchanges:
                        trans_ex += 1

                    else:
                        print('\n!!!!!!!!! Unknown transfer !!!!!!!!!!\n')

                if operation[0] == 'transfer_to_vesting':
                    trans_vest += 1
                    vesting += float(operation[1]['amount'].split()[0])

                if operation[0] == 'withdraw_vesting':
                    trans_withd += 1
                    withdraw += float(operation[1]['vesting_shares'].split()[0])
                        
                if operation[0] == 'feed_publish':
                    feed_count += 1
                    feed_time = time_diff / feed_count
                    feed_base = operation[1]['exchange_rate']['base']
                    
                if operation[0] == 'convert':
                    convert += 1
                    amount = operation[1]['amount'].split()
                    if amount[1] == 'STEEM':
                        convert_steem += float(amount[0])
                    if amount[1] == 'SBD':
                        convert_sbd += float(amount[0])
                    else:
                        print('\n!!! Unknown currency !!!\n')

                if from_ex_steem > 0:
                    steem_ex_flow = to_ex_steem / from_ex_steem
                else:
                    steem_ex_flow = 0

                if from_ex_sbd > 0:
                    sbd_ex_flow = to_ex_sbd / from_ex_sbd
                else:
                    sbd_ex_flow = 0    

                block_stats = {"block_interval": block_interval,
                    "block_number": start_block,
                    "last_block_time": last_block_time,
                    
                    "br": br,
                    "block_count": block_count, 
                    "dys_ts": dys_ts,
                    "time_diff": str(time_diff),
                    "dmin": dmin,
                    
                    "pow2_count": pow2_count,
                    "pow2_block": pow2_block,
                    "pow2_time": str(pow2_time),
                    
                    "trans_count": trans_count, 
                    "trans2ex": trans2ex,
                    "to_ex_steem": to_ex_steem,
                    "to_ex_steem_dmin": to_ex_steem/dmin,
                    "to_ex_sbd": to_ex_sbd,
                    "to_ex_sbd_dmin": to_ex_sbd/dmin,
                    
                    "trans4ex": trans4ex,
                    "from_ex_steem": from_ex_steem,
                    "from_ex_steem_dmin": from_ex_steem/dmin,
                    "from_ex_sb": from_ex_sbd,
                    "from_ex_sbd_dmin": from_ex_sbd/dmin,

                    "steem_ex_flow": steem_ex_flow,
                    "sbd_ex_flow": sbd_ex_flow,
                    "trans_u": trans_u,
                    "trans_e": trans_ex,

                    "trans_null": trans_null,
                    "to_null_sbd": to_null_sbd,
                    "to_null_sbd_dmin": to_null_sbd/dmin,

                    "trans_vest": trans_vest,
                    "vesting": vesting,
                    "vesting_dmin": vesting/dmin,

                    "trans_withd": trans_withd,
                    "withdraw": withdraw/1000/1000,
                    "withdraw_dmin": withdraw/1000/1000,

                    "convert": convert,
                    "convert_sbd": convert_sbd,
                    "convert_sbd_dmin": convert_sbd/dmin,

                    "feed_count": feed_count,
                    "feed_base": feed_base,
                    "feed_time": str(feed_time)
                }

                rdb.set("block_stats", json.dumps(block_stats))
                read_stats = json.loads( rdb.get("block_stats").decode() )
                #out = html_all % block_stats
                
    block_count += 1
    time.sleep(pause)

with open(index_file, 'w') as fl:
    fl.write(html_all % block_stats)

print('Parsed %s blocks for %s' % (block_count, str(time_diff)) )
