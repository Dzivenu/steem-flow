#!/usr/bin/python3
'''
Get data from Redis and aggregate together slot's records 
'''
import sys
import redis
import json
import yaml
import pprint

import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from numpy import arange

from get_redis import * 

# set font
mpl.rcParams["font.family"] = "serif"
mpl.rcParams["font.size"] = 16

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

xtics = arange(len(df.index))

#### 1
plt.figure(1)
plt.bar(xtics-0.2, df["to_ex_steem_dmin"],
            width=0.4,
            color="blue",
            label="spm to exchanges")
plt.bar(xtics+0.2, df["from_ex_steem_dmin"],
            width=0.4,
            color="lightblue",
            label="spm from exchanges")
plt.legend()
plt.xticks(xtics, df["dys_ts"], rotation = 90)
plt.title("STEEM flow rate")
plt.xlabel("Date")
plt.ylabel("STEEM per minute")
plt.autoscale(tight=True)
plt.subplots_adjust(bottom = 0.32)
plt.savefig("steem_ex.png")

#### 2
plt.figure(2)
plt.bar(xtics-0.2, df["to_ex_sbd_dmin"],
            width=0.4,
            color="blue",
            label="$pm to exchanges")
plt.bar(xtics+0.2, df["from_ex_sbd_dmin"],
            width=0.4,
            color="lightblue",
            label="$pm from exchanges")
plt.legend()
plt.xticks(xtics, df["dys_ts"], rotation = 90)
plt.title("SBD flow rate")
plt.xlabel("Date")
plt.ylabel("SBD per minute")
plt.autoscale(tight=True)
plt.subplots_adjust(bottom = 0.32)
plt.savefig("sbd_ex.png")

#### 3
plt.figure(3)
plt.bar(xtics-0.2, df["steem_ex_flow"],
            width=0.4,
            color="blue",
            label="STEEM to/from exchanges ratio")
plt.bar(xtics+0.2, df["sbd_ex_flow"],
            width=0.4,
            color="lightblue",
            label="SBD to/from exchanges ratio")
plt.plot([0,len(df.index)], [1,1], "r-")
plt.legend()
plt.xticks(xtics, df["dys_ts"], rotation = 90)
plt.title("To/From exchanges flow ratio")
plt.xlabel("Date")
plt.ylabel("Ratio")
plt.autoscale(tight=True)
plt.subplots_adjust(bottom = 0.32)
plt.savefig("flow_ratio.png")

#plt.show()
