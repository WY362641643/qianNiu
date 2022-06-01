#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv

import redis
import requests
import re
from loguru import logger
import json
from concurrent.futures import ThreadPoolExecutor
import threading
import time

from core.config import *


class ResSpider():
    def __init__(self, **kwargs):

        for k, v in kwargs.items():
            object.__setattr__(self, k, v)
        self.redis = redis.Redis(host='127.0.0.1', port=6379, db=0, decode_responses=True)

    def listen_broker_queue(self, timeout=0):
        """监听 broker 队列中的数据"""
        while True:
            try:
                user = self.redis.brpop('scrapy_broker_queue')
                if user:
                    if isinstance(user[1], bytes):
                        user = user[1].decode(encoding='utf-8')
                    else:
                        user = user[1]
                    try:
                        logger.info(f'Recv:{user}')
                        self.callback(user)
                    except Exception as e:
                        logger.exception(e)
                print('listening...')
            except Exception as e:
                logger.exception(e)

    def listen_orderId_queue(self, user, timeout=0):
        """监听 orderId 队列中的数据"""
        # 创建一个包含20条线程的线程池
        pool = ThreadPoolExecutor(max_workers=20)
        while True:
            try:
                data = self.redis.brpop('orderId:' + str(user))
                if data:
                    if isinstance(data[1], bytes):
                        data = data[1].decode(encoding='utf-8')
                    else:
                        data = data[1]
                    try:
                        logger.info(f'Recv:{data}')
                        # 向线程池提交一个task, 50会作为action()函数的参数
                        # future1 = pool.submit(self.get_requests_data, **{
                        #     **dict(user=user), **json.loads(data)
                        # })
                        self.get_requests_data(**{**dict(user=user), **json.loads(data)})
                    except Exception as e:
                        logger.exception(e)
                else:
                    # 此管道已不再添加数据, 不再监听此管道, 并删除对应的 str-headers
                    self.redis.delete('headers:' + str(user))
                    # 跳出监听
                    break
                print('listening...')
            except Exception as e:
                logger.exception(e)

    def get_order_start_time(self, *args):
        """获取下单时间"""
        for lines in args:
            # for line in lines:
            try:
                for content in lines['content']:
                    if content['value']['name'] == '创建时间:':
                        return content['value']['value']
            except:
                continue
        return None

    def get_tradeStatus(self, *args):
        """获取所有订单状态"""
        value = []
        for tradeStatues in args:
            for tradestatue in tradeStatues['tradeStatus']:
                for content in tradestatue['content']:
                    value.append(content['value'])
        return value

    def get_taobao_requests_data(self, headers, **kwargs):
        """通过旧页面获取数据"""
        url = self.linkAll['getDataUrlFormer'].format(orderId=kwargs.get('orderId')[0])
        logger.info(url)
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            try:
                res.encoding = 'gb18030'
                HTML = res.text
                recipient_name = re.search('收货地址：</th>.*?<td>(.*?)<', HTML, flags=re.S).group(1).replace(
                    ' ', '').replace('\t', '').replace('\r', '').replace('\n', '').split('，')
                logisticsNum = re.search('运单号：</th>.*?<td>(.*?)</td>.*?</tr>', HTML, flags=re.S).group(1).replace(
                    ' ', '').replace('\t', '').replace('\r', '').replace('\n', '')
                # 客户名称 唯一
                client_name = recipient_name[0]
                # 客户电话 唯一
                client_phone = recipient_name[1]
                # 客户地址 唯一
                client_address = recipient_name[3]
                # 成交价格 唯一
                totalPrice = float(re.search('<td class="order-price".*?>(.*?)<', HTML, flags=re.S).group(1))
                flots = re.search('<td class="post-fee" .*?>.*?(\d+\.\d+).*?</td>', HTML, flags=re.S).group(1)
                totalPrice += float(re.search('(\d+\.\d+)', flots, flags=re.S).group(1))
                # 下单时间 唯一
                order_start_time = re.search('class="trade-time">.*?(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*?<', HTML,
                                             flags=re.S).group(1)

                # 商品名称
                title = re.findall('<div class="desc">.*?<.*?><.*?>(.*?)<', HTML, flags=re.S)
                # 订单状态
                tradeStatus = re.findall('<td class="status">(.*?)<', HTML, flags=re.S)
                # 商品数量
                quantity = re.findall('<td class="num">(\d+)<', HTML, flags=re.S)
                for index in range(len(title)):
                    text = [
                        # 客户名称 唯一
                        client_name,
                        # 客户电话 唯一
                        client_phone,
                        # 客户地址 唯一
                        client_address,
                        # 下单时间 唯一
                        order_start_time,
                        # 订单号
                        kwargs.get('orderId')[0],
                        # 商品名称
                        title[index],
                        # 商品数量
                        quantity[index],
                        # 成交价格
                        str(totalPrice),
                        # 快递单号 唯一
                        logisticsNum,
                        # 订单状态
                        tradeStatus[index].replace(' ', '').replace('\t', '').replace('\r', '').replace('\n', ''),
                    ]
                    with open(kwargs.get('name'), "a", encoding="utf-8-sig", newline="") as f:
                        # 基于打开的文件，创建 csv.writer 实例
                        writer = csv.writer(f)
                        # 写入 header。
                        # writerow() 一次只能写入一行。
                        writer.writerow(text)
                        # 写入数据。
                        # writerows() 一次写入多行。
                        # writer.writerows(data_list)
                    logger.info(f'Writer:{text}')
            except Exception as e:
                with open('myTest/1.html', 'w', encoding='gb18030') as f:
                    f.write(HTML)
                logger.exception(e)
                with open(kwargs.get('nameError'), 'a', encoding='utf-8') as f:
                    f.write(kwargs.get('orderId')[0] + '\n')
        else:
            with open(kwargs.get('nameError'), 'a', encoding='utf-8') as f:
                f.write(kwargs.get('orderId')[0] + '\n')

    def get_requests_data(self, **kwargs):
        """通过 requests.get请求获取数据, 并存入文件中"""
        # kwargs = {'user': '哥两好小玉屋远方', 'name': 'D:\\Desktop\\project\\qianNiu\\appData\\哥两好小玉屋远方-a12345678_spider.csv', 'nameError': 'D:\\Desktop\\project\\qianNiu\\appData\\哥两好小玉屋远方-a12345678_error.txt', 'orderId': ['1493187795987894', '退款成功']}

        headers = json.loads(self.redis.get('header:' + str(kwargs.get('user'))))
        flag = re.findall(self.includeNoSpiderOrderStatus, kwargs.get('orderId')[1], flags=re.S)
        if not flag:
            logger.info('订单状态被过滤:',kwargs.get('orderId')[0])
            return
            # 轮询获取单个订单数据
        res = requests.get(self.linkAll['getDataUrl'].format(orderId=kwargs.get('orderId')[0]), headers=headers)
        if res.status_code == 200:
            try:
                order_data = res.json()
                if order_data.get('needJumpOld'):
                    self.get_taobao_requests_data(headers, **kwargs)
                    return
                recipient_name = order_data.get('tabs')[0]['content'].get('address').split('，')
                # 客户名称 唯一
                client_name = recipient_name[0]
                # 客户电话 唯一
                client_phone = recipient_name[1]
                # 客户地址 唯一
                client_address = recipient_name[2]
                # 快递单号 唯一
                try:
                    logisticsNum = order_data['tabs'][0]['content']['logisticsNum']
                except:
                    logisticsNum = None

                # 下单时间 唯一
                order_start_time = self.get_order_start_time(*order_data.get('mainOrder')['orderInfo']['lines'])

                # # 循环获取多个商品
                # for index, goods in enumerate(order_data.get('mainOrder')['subOrders']):
                #     # 商品名称
                #     title = goods['itemInfo']['title']
                #     # 商品数量
                #     quantity = goods['quantity']

                # 只获取一个商品
                # 商品名称
                title = order_data.get('mainOrder')['subOrders'][0]['itemInfo']['title']
                # 商品数量
                quantity = order_data.get('mainOrder')['subOrders'][0]['quantity']
                # 成交价格
                totalPrice = 0
                for price in order_data['mainOrder']['totalPrice']:
                    try:
                        totalPrice += float(re.findall('\d+\.\d+', price['content'][0]['value'], flags=re.S)[0])
                    except:
                        pass
                # 订单状态
                tradeStatus = self.get_tradeStatus(*order_data['mainOrder']['subOrders'])
                # 快递名称
                logisticsName = order_data['tabs'][0]['content']['logisticsName']
                text = [
                    # 客户名称 唯一
                    client_name,
                    # 客户电话 唯一
                    client_phone,
                    # 客户地址 唯一
                    client_address,
                    # 下单时间 唯一
                    order_start_time,
                    # 订单号
                    # kwargs.get('orderId')[0],
                    # 商品名称
                    title,
                    # 商品数量
                    quantity,
                    # 成交价格
                    str(totalPrice),
                    # 快递单号 唯一
                    logisticsNum,
                    # 订单状态
                    tradeStatus,
                    # 快递名称
                    logisticsName,
                ]
                with open(kwargs.get('name'), "a", encoding="utf-8-sig", newline="") as f:
                    # 基于打开的文件，创建 csv.writer 实例
                    writer = csv.writer(f)
                    # 写入 header。
                    # writerow() 一次只能写入一行。
                    writer.writerow(text)
                    # 写入数据。
                    # writerows() 一次写入多行。
                    # writer.writerows(data_list)
                logger.info(f'Writer:{text}')
            except Exception as e:
                logger.exception(e)
                with open(kwargs.get('nameError'), 'a', encoding='utf-8') as f:
                    f.write(kwargs.get('orderId')[0] + '\n')
        else:
            with open(kwargs.get('nameError'), 'a', encoding='utf-8') as f:
                f.write(kwargs.get('orderId')[0] + '\n')

    def callback(self, user):
        """获取到 redis 主队列中数据, 启动采集"""
        self.listen_orderId_queue(user)


if __name__ == '__main__':
    data = config['qianNiu']
    resSpider = ResSpider(**data)
    resSpider.listen_orderId_queue('ali088602014831阿紫')
    # resSpider.listen_broker_queue()
    # resSpider.get_requests_data()
