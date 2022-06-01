#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import csv

with open(r'C:\Users\Administrator\Desktop\qianNiu\appData/ali088602014831阿紫-qiuyuan888_spider.csv', 'r',
          encoding='gb18030') as f:
    reads = csv.reader(f)
    data = [row for row in reads]
with open('1.txt', 'a', encoding='utf-8') as f:
    for row in data:
        row[4] = row[4].rstrip('0000 ')
        f.write(' '.join(row) + '\n')
