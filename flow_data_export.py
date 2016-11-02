#!/usr/bin/python3
'''
Get data from Redis and save it to Pandas dataframe
'''
import sys
import redis
import json
import yaml
import pprint
import pandas as pd

from get_redis import * 

# config
my_config = yaml.load(open("steemapi.yml"))
log = my_config['log']
prefix = my_config["prefix"]
last_info = my_config["last_info"]
blocks_list = my_config["blocks_list"]

rdb = redis.Redis(host="localhost", port=6379)
pp = pprint.PrettyPrinter(indent=4)

# from cli
start_block = int(sys.argv[1])
end_block   = int(sys.argv[2])

slot_list = get_list(rdb, prefix + blocks_list, start_block, end_block)
#pp.pprint(slot_list)
df = pd.DataFrame()
for redis_key in slot_list:
    print(redis_key)
    read_stats = json.loads( rdb.get(redis_key).decode() )
    #pp.pprint(read_stats)
    data = pd.DataFrame.from_dict([read_stats])
    df = df.append(data)

print(df, df.columns.values)

df.to_pickle("store.pkl")
