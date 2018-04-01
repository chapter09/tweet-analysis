
# coding: utf-8


import csv
import os
import pandas as pd
import twitter
import numpy as np
import time
from multiprocessing import cpu_count, Pool
 
cores = cpu_count() # Number of CPU cores on your system
partitions = cores # Define as many partitions as you want
batch_num = 10000 # The size of api.GetStatus input list


tw_df = pd.read_csv("../data/raw/dev.txt", delimiter='\t', names=['t_id', 'emotion'])
tw_df.shape

api = twitter.Api(consumer_key='yylWBvKsFiT6TVutxDtw7gW9W',
                  consumer_secret='Z3tdgCzqMn5YYC38xzhShpMQVcH340WUzevRANmBGM0Di8rDfs',
                  access_token_key='82013415-pX5ss0oBh37aFm3jgBI0JxSls1DVIltroLZl0PgdI',
                  access_token_secret='UdkJwLWkT5a5Bk3Ej5eTqlOuBmtU8WV0DeekLQWwDSmXo',
                  sleep_on_rate_limit=True)
 

def parallelize(df, func):
    df_split = np.array_split(df, partitions)
    pool = Pool(cores)
    data = np.concatenate(pool.map(func, df_split))
    pool.close()
    pool.join()
    return data.tolist()


def get_statuses(df):
    try:
        return np.asarray(api.GetStatuses(df['t_id']))
    except twitter.error.TwitterError as e:
        print(e)
        print(" Start sleeping...")
        time.sleep(900)
        print("Wake up")
        return get_statuses(df)

    
def parse_status(s_list):
    tw_list = [(s.id, s.text) for s in s_list]
    tw_df = pd.DataFrame.from_records(tw_list, columns=["t_id", "status"])
    return tw_df
    
    
def load_tweets(in_fname, out_fname):
    print("Load " + in_fname)
    tw_df = pd.read_csv(in_fname, delimiter='\t', names=['t_id', 'emotion'])
    record_num = tw_df.shape[0]
    epoch_size = int(record_num / (batch_num * cores)) + 1

    out_fd = open(out_fname, 'a')
    for i in range(0, epoch_size):
        print("Processing %d - %d" % (i*batch_num*cores, (i+1)*batch_num*cores))
        if (i+1)*batch_num*cores < record_num:
            parse_status(parallelize(tw_df[i*batch_num*cores: (i+1)*batch_num*cores], 
                                     get_statuses)).to_csv(out_fd, header=False)
        else:
            print(i*batch_num*cores)
            parse_status(parallelize(tw_df[i*batch_num*cores:], 
                                     get_statuses)).to_csv(out_fd, header=False)
            out_fd.flush()
    out_fd.close()
    print("Done")


file_list = [
    "dev.txt",
    #"test.txt",
    #"train_1.txt",
    #"train_2_10.txt",
    #"train_2_1.txt",
    #"train_2_2.txt",
    #"train_2_3.txt",
    #"train_2_4.txt",
    #"train_2_5.txt",
    #"train_2_6.txt",
    #"train_2_7.txt",
    #"train_2_8.txt",
    #"train_2_9.txt"
]

for f in file_list:
    load_tweets("../data/raw/" + f, "/mnt/tweets/" + os.path.splitext(f)[0] + "-parsed-r.csv")

