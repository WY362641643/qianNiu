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
import sys


class ResSpider():
    def __init__(self, **kwargs):

        for k, v in kwargs.items():
            object.__setattr__(self, k, v)
        self.redis = redis.Redis(host='127.0.0.1', port=6379, db=0, decode_responses=True)

    def listen_broker_queue(self, timeout=0):
        """监听 broker 队列中的数据"""
        # 创建一个包含20条线程的线程池
        pool = ThreadPoolExecutor(max_workers=20)
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
                        # 向线程池提交一个task, 50会作为action()函数的参数
                        # 将发包任务添加进 进程池
                        # 多线程
                        # future1 = pool.submit(self.callback, **user)
                        # 单线程采集
                        self.callback(user)
                    except Exception as e:
                        logger.exception(e)
                print('listening...')
            except Exception as e:
                logger.exception(e)

    def listen_orderId_queue(self, user, timeout=0):
        """监听 orderId 队列中的数据"""
        while True:
            try:
                child_data = self.redis.brpop('orderId:' + str(user))
                if child_data:
                    if isinstance(child_data[1], bytes):
                        child_data = child_data[1].decode(encoding='utf-8')
                    else:
                        child_data = child_data[1]
                    try:
                        logger.info(f'Recv:{child_data}')
                        # 获取错误文件路径
                        if child_data:
                            child_data = json.loads(child_data)
                            nameError = child_data.get('nameError')
                            self.get_requests_data(**{**dict(user=user), **child_data})
                    except Exception as e:
                        logger.exception(e)
                else:
                    # 获取错误文件内的数据
                    with open(nameError, 'r', encoding='utf-8') as f:
                        error_child_data = f.read()
                    # 将错误文件清零
                    with open(nameError, 'w', encoding='utf-8') as f:
                        f.write('')
                    error_child_data = error_child_data.split('\n')
                    # 重新获取错误数据
                    for child_data in error_child_data:
                        self.get_requests_data(**{**dict(user=user), **eval(child_data)})
                    # 此管道已不再添加数据, 不再监听此管道, 并删除对应的 str-headers
                    self.redis.delete('headers:' + str(user))
                    # 关闭线程
                    sys.exit()
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
        url = self.linkAll['getDataUrlFormer'].format(orderId=kwargs.get('child_data')[0])
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
                if '*' in client_phone:
                    # 电话号码中含有 * 不采集此电话号码
                    raise ValueError
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
                        writer.writerow(text)
                        # 写入数据。
                    logger.info(f'Writer:{text}')
            except Exception as e:
                with open(kwargs.get('nameError'), 'a', encoding='utf-8') as f:
                    f.write(kwargs.get('child_data') + '\n')
        else:
            with open(kwargs.get('nameError'), 'a', encoding='utf-8') as f:
                f.write(kwargs.get('child_data') + '\n')

    def get_requests_data(self, **kwargs):
        """通过 requests.get请求获取数据, 并存入文件中"""
        headers = json.loads(self.redis.get('header:' + str(kwargs.get('user'))))
        flag = re.findall(self.includeNoSpiderOrderStatus, kwargs.get('child_data')[1], flags=re.S)
        if not flag:
            logger.info('订单状态被过滤:', kwargs.get('child_data')[0])
            return
            # 轮询获取单个订单数据
        res = requests.get(self.linkAll['getDataUrl'].format(orderId=kwargs.get('child_data')[0]), headers=headers)
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
                if '*' in client_phone:
                    # 电话号码中含有 * 不采集此电话号码
                    raise ValueError
                # 客户地址 唯一
                client_address = recipient_name[2]
                # 快递单号 唯一
                try:
                    logisticsNum = order_data['tabs'][0]['content']['logisticsNum']
                except:
                    logisticsNum = None
                # 商品名称
                title = order_data.get('mainOrder')['subOrders'][0]['itemInfo']['title']
                # 快递名称
                logisticsName = order_data['tabs'][0]['content']['logisticsName']
                text = [
                    # 客户名称 唯一
                    client_name,
                    # 客户地址 唯一
                    client_address,
                    # 客户电话 唯一
                    client_phone,
                    # 商品名称
                    title,
                    # 成交价格
                    kwargs.get('child_data')[3],
                    # 商品数量
                    kwargs.get('child_data')[4],
                    # 订单状态
                    kwargs.get('child_data')[1],
                    # 快递名称
                    logisticsName,
                    # 快递单号 唯一
                    logisticsNum,
                    # 下单时间 唯一
                    kwargs.get('child_data')[2],
                ]
                with open(kwargs.get('name'), "a", encoding="utf-8-sig", newline="") as f:
                    # 基于打开的文件，创建 csv.writer 实例
                    writer = csv.writer(f)
                    writer.writerow(text)
                    # writerows() 一次写入多行。
                logger.info(f'Writer:{text}')
            except Exception as e:
                logger.exception(e)
                with open(kwargs.get('nameError'), 'a', encoding='utf-8') as f:
                    f.write(str(kwargs.get('child_data')) + '\n')
        else:
            with open(kwargs.get('nameError'), 'a', encoding='utf-8') as f:
                f.write(str(kwargs.get('child_data')) + '\n')

    def callback(self, user):
        """获取到 redis 主队列中数据, 启动采集"""
        self.listen_orderId_queue(user)


if __name__ == '__main__':
    data = config['qianNiu']
    resSpider = ResSpider(**data)
    # resSpider.listen_orderId_queue('ali088602014831阿紫')
    resSpider.listen_broker_queue()
    # resSpider.get_requests_data()
