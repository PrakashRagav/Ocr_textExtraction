import csv 
import pandas as pd
import pathlib
import os 

temp = pathlib.PosixPath
pathlib.PosixPath = pathlib.WindowsPath
path = pathlib.Path.cwd()
csv_path = pathlib.PosixPath(path,'csv')
csv_list = list(csv_path.glob('**\*csv'))

for csv_i in csv_list:
    df = pd.read_csv(csv_i)
    copy = []
    for i in df.values:
        np_list = i.tolist()
        np_list = np_list[-1:]+np_list[:-1]
        copy.append(np_list)
    with open(csv_i, 'w',encoding='utf_8_sig',newline='') as f:
            write = csv.writer(f)
            write.writerows(copy)
