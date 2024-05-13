# -*- coding: utf-8 -*-
'''
@File  : em_chrom.py
@Author: Stone
@Date  : 2023/12/14 9:55
'''
import chromadb

import json
import requests
headers = {'Content-Type': 'application/json'}
data = {"question":"请分析丹东所有华为基站的top10高隐患基站情况"}
response = requests.post('http://127.0.0.1:5000/query', headers=headers, data=json.dumps(data))
response1 = response.json()
print(
    response1
)
response = response.text
print(response)
