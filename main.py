#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from loguru import logger
from selenium import webdriver
import copy
import time
import os.path
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, ElementNotVisibleException
from selenium.common.exceptions import StaleElementReferenceException, InvalidSelectorException
from selenium.common.exceptions import WebDriverException, TimeoutException, ElementClickInterceptedException
from selenium.common.exceptions import ElementNotInteractableException, NoSuchWindowException
from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.common.action_chains import ActionChains
# from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service

import re
import json
import redis
# from core.utils import getDateTimeFromStr, Lock, JsonEncoder
# from core.mc import MongoClientPlus
# from core.rc import getRedisClient
# from core.error_handler import *
from core.message import SpiderMessage
# from spider.core.basehandler import BaseRequest
# from com import logger, app_data_path, config
# from core.utils import JsonEncoder

from core.setting import *
from core.config import *
import datetime


class BaseWebDriver:
    """
    基于selenium框架的模拟浏览器方式进行数据采集
    """

    def __init__(self, **kwargs):
        self._state_ = SpiderMessage.Status.INIT
        self._spider_status_ = 0  # 定义数据采集进度状态
        self.__msg_queue__ = []
        self.workspace_path = app_data_path
        self._create_workspace_(self.workspace_path)
        self.selector_tag = {
            'id': By.ID,
            'class': By.CLASS_NAME,
            'class name': By.CLASS_NAME,
            'xpath': By.XPATH,
            'css': By.CSS_SELECTOR,
            'name': By.NAME,
            'tag_name': By.TAG_NAME,
            'link_text': By.LINK_TEXT
        }
        self.paging = 0  # 定义已经采集完成的页码
        self.format = {
            'code': self._state_
        }
        for k, v in kwargs.items():
            object.__setattr__(self, k, v)
        self.name = (self.user + '-' + self.pwd).replace('\\', '').replace('/', '').replace(':', '').replace(
            '*', '').replace('?', '').replace('<', '').replace('>', '').replace('"', '').replace('|', '')
        self.fileName = os.path.join(self.workspace_path, self.name + '_spider.csv')
        self.fileNameError = os.path.join(self.workspace_path, self.name + '_error.txt')

        self.redis = redis.Redis(host='127.0.0.1', port=6379, db=0, decode_responses=True)
        self.userName = self.user.replace('\\', '').replace('/', '').replace(':', '').replace(
            '*', '').replace('?', '').replace('<', '').replace('>', '').replace('"', '').replace('|', '')
        # 通知主管道, 有任务产生
        self.redis.lpush('scrapy_broker_queue', str(self.userName))

        # 获取起始年份, 月份和日期
        self.start_year = datetime.datetime.now().year
        self.start_month = datetime.datetime.now().month
        if self.start_month < 3:
            if self.start_month == 1:
                self.start_month = 11
                self.start_year -= 1
            else:
                self.start_month = 12
                self.start_year -= 1
        else:
            self.start_month -= 3
        self.start_day = datetime.datetime.now().day
        if len(str(self.start_month)) < 2:
            self.start_month = '0' + str(self.start_month)
        if len(str(self.start_day)) < 2:
            self.start_day = '0' + str(self.start_day)

        self.end_data = f'{self.start_year}-{self.start_month}-{self.start_day} 00:00:00'

    def __setattr__(self, key, value):
        object.__setattr__(self, key, value)

    def __getattr__(self, item):
        return self.__dict__.get(item, None)

    @staticmethod
    def _create_workspace_(path):
        """生成路径"""
        if not os.path.exists(path):
            os.makedirs(path)

    def __init_webdriver__(self, **kwargs):
        """初始化浏览器对象"""
        if self._state_ >= SpiderMessage.Status.READY:
            # 此步骤已执行
            return
        chrome_options = webdriver.ChromeOptions()
        # chrome_options.add_experimental_option('w3c', False)  # selenium 版本4.0以上需要注释掉
        # caps = DesiredCapabilities.CHROME
        # caps['loggingPrefs'] = {'performance': 'ALL'}
        # chrome_options.add_argument("-headless")  # 使用无头模式（也就是无窗口运行）
        # chrome_options.add_argument('lang=zh_CN.UTF-8')  # 设置语言与编码
        # chrome_options.add_argument('user-agent="你要设定的UA"')  # 给driver设置UA，可以用来模拟手机端访问
        # dic = {"profile.managed_default_content_settings.images": 2}
        # chrome_options.add_experimental_option("prefs", dic)  # 设置driver不加载图片
        # chrome_options.add_argument("--proxy-server=" + self.IP)  # 添加代理IP
        # 设置 get 请求不等待 js css等静态文件加载
        # desired_capabilities = DesiredCapabilities.CHROME
        # desired_capabilities["pageLoadStrategy"] = "none"
        # 解决证书失效问题
        # 消除 selenium 的标记特征  屏蔽webdriver特征  start ======
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_argument("--disable-blink-features")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option('useAutomationExtension', False)
        # 消除特征 end ====
        chrome_options.add_argument('--ignore-certificate-errors')
        # 如果是需要带帐号密码验证的代理服务器 需要用chrome的插件解决（据说firefox的driver可以直接带参
        s = Service(self.driverPath)
        self.driver = webdriver.Chrome(
            # desired_capabilities=caps,
            # desired_capabilities=desired_capabilities,
            service=s,
            options=chrome_options)  # 一切设置完之后，只要在启动driver时带上options就可以了
        # self.driver.maximize_window()
        # 消除 selenium 的标记特征  屏蔽webdriver特征  start ======
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
            Object.defineProperty(navigator, 'webdriver', {
              get: () => undefined
            })
          """
        })
        # 消除特征 end ====

        self.webDriverTimeout = self.timeout["webDriverTimeout"] if self.timeout["webDriverTimeout"] is not None else 30
        self.wait = WebDriverWait(self.driver, self.webDriverTimeout)
        self._state_ = SpiderMessage.Status.READY

    def __writer_redis_queue__(self, *args):
        """将数据写入redis管道"""
        # 将orderId存入redis
        self.redis.lpush('orderId:' + str(self.userName), *[json.dumps({
            'name': self.fileName,
            'nameError': self.fileNameError,
            'child_data': child_data
        }, ensure_ascii=False, indent=4) for child_data in args])

        # 更新请求头
        cookieds = self.driver.get_cookies()
        self.cookie = ''
        for cookieDicr in cookieds:
            self.cookie += cookieDicr['name'] + '=' + cookieDicr['value'] + '; '
        self.headers['cookie'] = self.cookie
        self.redis.set('header:' + str(self.userName), json.dumps(self.headers, ensure_ascii=False, indent=4)
                       )

    def __get_redis_queue_number__(self):
        """获取管道中未采集的数量"""
        number = 1000
        while number > self.push_number:
            try:
                number = self.redis.llen('orderId:' + str(self.userName))
            except Exception as e:
                logger.exception(e)
            time.sleep(1)

    def __finish__(self):
        """采集完成, 改变状态, 通知reids队列, 关闭浏览器"""
        if self._spider_status_ == SpiderMessage.QNSpiderPoint.SHOP_FINISH:
            # 改变流程状态
            self._state_ = SpiderMessage.Status.FINISH
            # 通知 redis 管道
            self.redis.lpush('orderId:' + str(self.userName), '')
            self.__flush_msg_queue__(
                **SpiderMessage.Finish.__dict__
            )
            return True

    def parse_waiting_condition(self, by=None, value=None, **kwargs):
        """配置 wait需要的 标签的 匹配键和值"""
        if by is None or value is None or by not in self.selector_tag.keys():
            email_msg = dict(status=4041, subject='wait阻塞等待标签选择错误', content=f"不存在该类型的匹配方式, 标签内容: {kwargs}")
            self.__flush_msg_queue__(
                errorlevel=SpiderMessage.ErrorLevel.__dict__['Critical'], sattus=400, data=email_msg,
                msg=f"{email_msg.get('subject')}, 等待人工处理", **SpiderMessage.LoginInitFailed.__dict__
            )
            return False
        return self.selector_tag[by], value

    def parse_element_condition(self, by=None, value=None, **kwargs):
        """配置 find_element 的参数格式化"""
        if by is None or value is None or by not in self.selector_tag.keys():
            email_msg = dict(status=4041, subject='find_element 标签错误事件', content=f"不存在该类型的匹配方式, 标签内容: {kwargs}")
            self.__flush_msg_queue__(
                errorlevel=SpiderMessage.ErrorLevel.__dict__['Critical'], status=400, data=email_msg,
                msg=f"{email_msg.get('subject')}, 等待人工处理", **SpiderMessage.LoginInitFailed.__dict__
            )
            return False
        return dict(by=self.selector_tag.get(by, By.ID), value=value)

    def slide_page_top(self):
        """将页面滑动至顶部"""
        try:
            # 滚动条滑动至顶部
            self.driver.execute_script("var q=document.documentElement.scrollTop=0")
        except WebDriverException as e:
            # 当有悬浮标签时, 此功能会出现 WebDriverException 异常
            pass

    def slide_page_bottom(self):
        """将页面滑动至底部"""
        try:
            self.driver.execute_script("var q=document.documentElement.scrollTop=100000")
        except WebDriverException as e:
            # 当有悬浮标签时, 此功能会出现 WebDriverException 异常
            pass

    @staticmethod
    def parse_element_to_waiting_condition(by, value, **kwargs):
        """将需要操作的element标签的键值转换成阻塞等待需要的键值"""
        return {**kwargs, **{'key': by, 'value': value}}

    def __get_login_page__(self):
        """
        打开登录页面：
        1.提取所有的登录方式及其输入要素
        :return:
        """
        if self._state_ >= SpiderMessage.Status.LOGIN:
            # 此步骤已执行
            return True
        print('启动刘浏览器')
        self.driver.get(self.linkAll['loginUrl'])
        handles = self.driver.window_handles
        # 获取新打开的窗口句柄
        for handle in handles:
            self.window_handle = handle
        try:
            # 等待监听登登录窗口打开成功
            self.block_waiting(**self.loginTag['getLoginSuccess'])
        except Exception as e:
            error_msg = f'登录页面打开失败，请联系管理员({e})'
            logger.error(error_msg)
            # 打开登录页面失败
            email_msg = dict(status=400, subject='登录首页打开失败', content=error_msg)
            self.__flush_msg_queue__(
                errorlevel=SpiderMessage.ErrorLevel.__dict__['Critical'], msg=f"{email_msg.get('subject')}, 等待人工处理",
                sattus=400, data=email_msg, **SpiderMessage.LoginInitFailed.__dict__
            )
            return False
        self._state_ = SpiderMessage.Status.LOGIN
        return True

    def __flush_msg_queue__(self, **kwargs):
        self.format = kwargs

    def __collect__(self, **kwargs):
        """执行数据采集的函数"""
        while self._state_ < SpiderMessage.Status.FINISH:
            print('开始采集数据')
            try:
                # 跳转到 已卖出宝贝的地址
                self.driver.get(self.linkAll['outGoods'])
                # 获取最近三个月的订单
                if self.__get_data_lately_trimester__(**kwargs):
                    self._spider_status_ = SpiderMessage.QNSpiderPoint.SHOP_FINISH
                # 获取三个月以外的订单
                # self.__get_data_lately_trimester_except__(**kwargs)
                # 查看是否采集完成
                if self.__finish__():
                    flag = input('已经采集完成, 直接点击回车关闭浏览器, 或者输入任意字符, 重新采集:')
                    if not flag:
                        # 关闭刘浏览器
                        self.driver.quit()
                        return True
                    else:
                        self._spider_status_ = SpiderMessage.QNSpiderPoint.START
                        self._state_ = SpiderMessage.Status.COLLECT
            except Exception as e:
                logger.exception(e)
                input('发生位置错误， 请联系开发人员')

    def __get_data_lately_trimester__(self, **kwargs):
        """获取近三个月的订单"""
        if self._spider_status_ >= SpiderMessage.QNSpiderPoint.LATELY_TRIMESTER:
            # 此步骤已执行
            return
        # 点击交易和已卖出的宝贝
        # if self.is_element_exist(**self.getDataClickTag['clickCommodity']):
        #     self.click_browser_page(self.getDataClickTag['clickCommodity'], self.getDataClickTag['clickSold'])
        # # 点击最近三个月订单
        # self.click_element(**self.getDataClickTag['clickLatelyTrimester'])
        # 进入循环, 开始批量获取数据
        order_start_time = []
        input('进入最近三个月订单页面后回车')
        while True:
            # 等待加载标签消失
            self.block_not_waiting(**self.getDataTagDoing['next_page_loading'])
            # 获取当前页数
            page = int(self.get_element_inner_text(**self.getDataTag['get_paging']))
            if self.paging_trimester >= page:
                # 跳转到指定页面
                self.click_skipping_number_page(self.getDataTag['pages_tag'], self.paging_trimester + 1)
                continue
            # 获取当前页面的源码
            HTML = self.get_page_source()
            # 获取当前页面源码中的订单号
            orderId = re.findall('订单号：(.*?)<', HTML, flags=re.S)
            if orderId:
                # 获取当前页面的订单状态
                orderStatus = self.get_elements_inner_text(**self.getDataTag['orderStatus'])
                # 获取当前页面的价格
                orderPrice = self.get_elements_inner_text(**self.getDataTag['orderPrice'])
                # 获取订单数量
                orderNumber = self.get_elements_inner_text(**self.getDataTag['orderNumber'])
                # 获取创建时间
                order_start_time = re.findall('创建时间：(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})<', HTML, flags=re.S)
                orderIds = list(zip(orderId, orderStatus, order_start_time, orderPrice, orderNumber))
                self.__writer_redis_queue__(*orderIds)
            print(f'获取近三个月的订单, 第{page}页')
            # 等待redis队列中的数据量少于 self.push_number 的数量
            self.__get_redis_queue_number__()
            # 判断下一页是否可点击
            if self.next_page(self.getDataClickTag['click_next_page']):
                self.paging_trimester = page
            else:
                if order_start_time[-1] < self.end_data:
                    print('已经采集完成最近三个月的数据')
                    # 跳出循环, 超过三个月
                    return True
                else:
                    # 点击更多
                    if self.is_element_exist(**self.getDataClickTag['morePages']):
                        self.click_element(**self.getDataClickTag['morePages'])
                        self.pageRefreshMax -= 1
                        if self.pageRefreshMax:
                            continue
                        return True
                    else:
                        # 没有更多页面了, 跳出循环
                        return True
        # self._spider_status_ = SpiderMessage.QNSpiderPoint.LATELY_TRIMESTER

    def __get_data_lately_trimester_except__(self, **kwargs):
        """获取近三个月以外的订单"""
        if self._spider_status_ >= SpiderMessage.QNSpiderPoint.LATELY_TRIMESTER_EXCEPT:
            # 此步骤已执行
            return
        # 点击交易和已卖出的宝贝
        self.click_browser_page(self.getDataClickTag['clickCommodity'], self.getDataClickTag['clickSold'])
        # 点击最近三个以外的月订单
        self.click_element(**self.getDataClickTag['clickLatelyTrimesterExcept'])
        time.sleep(1)
        # 进入循环, 开始批量获取数据
        while True:
            # 等待加载标签消失
            self.block_not_waiting(**self.getDataTagDoing['next_page_loading'])
            # 等待数据加载成功
            self.block_waiting(**self.getDataClickTag['dataShow'])
            # 获取当前页数
            page = int(self.get_element_inner_text(**self.getDataTag['get_paging']))
            if self.paging_trimester >= page:
                # 跳转到指定页面
                self.click_skipping_number_page(self.getDataTag['pages_tag'], self.paging_trimester + 1)
                continue
            # 获取当前页面的源码
            HTML = self.get_page_source()
            # 获取当前页面源码中的订单号
            orderId = re.findall('订单号：(.*?)<', HTML, flags=re.S)
            if orderId:
                # 获取当前页面的订单状态
                orderStatus = self.get_elements_inner_text(**self.getDataTag['orderStatus'])
                orderIds = list(zip(orderId, orderStatus))
                self.__writer_redis_queue__(*orderIds)
            print(f'获取近三个月以外的订单, 第{page}页')
            # 判断下一页是否可点击
            if self.next_page(self.getDataClickTag['click_next_page']):
                self.paging_trimester = page
            else:
                break
        self._spider_status_ = SpiderMessage.QNSpiderPoint.SHOP_FINISH

    def run(self):
        """
        数据采集任务的执行入口
        :return:
        """
        self.__init_webdriver__()
        while self._state_ != SpiderMessage.Status.FINISH and self._spider_status_ != SpiderMessage.QNSpiderPoint.SHOP_FINISH:
            try:
                # 1.打开登录页面
                if not self.__get_login_page__():
                    print('打开登录页面失败')
                    continue
                # # 2. 输入账户密码
                # if not self.__send_account_pwd__():
                #     print('输入账户密码页面失败')
                #     continue
                # 定义状态为开始采集订单
                self._state_ = SpiderMessage.Status.COLLECT
                # 3. 采集数据
                if not self.__collect__():
                    print('采集数据失败')
                    continue
            except Exception as e:
                logger.exception(e)
                input('程序发生错误')

    def block_waiting(self, **kwargs):
        """
        阻塞等待标签加载成功
        :return:
        """
        try:
            # 阻塞, 等待注册成功
            self.wait.until(
                EC.presence_of_element_located(
                    self.parse_waiting_condition(**kwargs)
                ))
            return True
        except (ElementClickInterceptedException, TimeoutException) as e:
            logger.exception(e)
            email_msg = dict(status=4041, subject='阻塞等待事件标签错误', content=f"页面未检测到该标签, 标签内容: {kwargs}")
            self.__flush_msg_queue__(
                errorlevel=SpiderMessage.ErrorLevel.__dict__['Critical'], msg=f"{email_msg.get('subject')}, 等待人工处理",
                sattus=400, data=email_msg, **SpiderMessage.LoginInitFailed.__dict__
            )
            self.__get_data_click_exception_tag__()
            return False

    def block_not_waiting(self, **kwargs):
        """
        阻塞等待标签消失
        :return:
        """
        try:
            self.wait.until_not(
                EC.presence_of_element_located(
                    self.parse_waiting_condition(**kwargs)
                ))
            return True
        except TimeoutException as e:
            # 标签阻塞等待检测失败
            logger.warning(e.msg)
            email_msg = dict(status=4041, subject='阻塞等待事件标签标签消失超时', content=f"阻塞等待事件标签标签消失超时, 标签内容: {kwargs}")
            self.__flush_msg_queue__(
                errorlevel=SpiderMessage.ErrorLevel.__dict__['Critical'], msg=f"{email_msg.get('subject')}, 等待人工处理",
                sattus=400, data=email_msg, **SpiderMessage.LoginInitFailed.__dict__
            )
            return False
        except ElementClickInterceptedException as e:
            logger.warning(e.msg)
            email_msg = dict(status=4041, subject='阻塞等待事件标签标签消失错误', content=f"页面未检测到该标签, 标签内容: {kwargs}")
            self.__flush_msg_queue__(
                errorlevel=SpiderMessage.ErrorLevel.__dict__['Critical'], msg=f"{email_msg.get('subject')}, 等待人工处理",
                sattus=400, data=email_msg, **SpiderMessage.LoginInitFailed.__dict__
            )
        except Exception as e:
            logger.warning(e.args)
            return False

    def is_element_exist(self, **kwargs):
        """
        用来判断元素标签是否存在，
        """
        try:
            element = self.driver.find_element(**self.parse_element_condition(**kwargs))
        except (ElementClickInterceptedException, NoSuchElementException) as e:
            return False
        else:
            # 没有发生异常，表示在页面中找到了该元素，返回True
            return element

    def click_browser_page(self, tag, child_tag=None, **kwargs):
        """等待标签加载后点击切换页面"""
        self.slide_page_top()
        # 一次点击右侧主菜单栏
        self.click_element(**tag)
        if child_tag is not None:
            time.sleep(0.5)
            try:
                # 二次点击右侧菜单栏的子菜单
                self.click_element(**child_tag)
            except NoSuchElementException as e:
                # logger.exception(e)
                # 二次次点击未成功, 没有这样的元素无法定位 Message: no such element: Unable to locate element
                # 1. 应悬浮标签的原因, 一次点击未成功, 二次点击时处理了悬浮标签; 但是没有检测到二次点击的悬浮标签, 这种情况重新执行函数解决
                return self.click_browser_page(tag, child_tag, **kwargs)

    def next_page(self, click_next_page, **kwargs):
        """
        点击下一页
        @param next_tag:
        @param kwargs:
        @return:
        """
        # 滑动至底部
        self.slide_page_bottom()
        try:
            if self.is_element_exist(**click_next_page).is_enabled():
                self.click_element(**click_next_page)
                return True
            else:
                return False
        except AttributeError:
            return False

    def click_skipping_number_page(self, pages_tag, page_number):
        """
        点击页面标签, 切换至指定页面
        @param pages_tag: 显示的可点击的页面标签匹配路径
        @param page_number: 跳转到的目标页码
        @return:
        """
        self.slide_page_bottom()
        # 查看是否出现 能输入页面的input标签 并且不存在 点击更多页面的标签
        if self.is_element_exist(**self.getDataClickTag['send_arriver_paging']):
            # 输入跳转标签的值
            self.send_element(page_number, **self.getDataClickTag['send_arriver_paging'])
            # 点击跳转
            self.click_element(**self.getDataClickTag['click_arriver_paging'])
            return page_number
        else:
            # 点击更多页面
            self.click_element(**self.getDataClickTag['morePages'])
            pass
            # # 获取所有 可点击页面的标签
            # elements = self.driver.find_elements(**self.parse_element_condition(**pages_tag))
            # # 获取所有对象的值
            # elements_value = self.get_elements_inner_text(**pages_tag)
            # elements_dict = dict(zip(elements_value, elements))
            # # 循环对比值, 点击最接近 page_number 的数
            # difference_value = 1000000000  # 定义初始化差值, 最大化
            # page_click_element_obj = None  # 定义点击页面的变量
            # for element_number, element_obj in elements_dict.items():
            #     if abs(int(element_number) - page_number) < difference_value:
            #         difference_value = abs(int(element_number) - page_number)
            #         page_click_element_obj = element_obj
            #     elif int(element_number) == page_number:
            #         # 获取到需要跳转的页面
            #         element_obj.click()
            #         # 返回跳转到的页面, 并赋值给page
            #         return element_number
            # # 未获取到指定页面, 跳转到最近一个可点击的页面, 然后重新执行
            # page_click_element_obj.click()
            # return self.click_skipping_number_page(pages_tag, page_number)

    def click_element(self, index=5, **kwargs):
        """点击事件"""
        try:
            element_obj = self.driver.find_element(**self.parse_element_condition(**kwargs))
            element_obj.click()
        except ElementNotVisibleException as e:
            if self.is_login_success_disposable(**kwargs) and index:
                # 登陆成功, 查看异常标签
                # self.__exception__element__(**kwargs)
                self.__get_data_click_exception_tag__(**kwargs)
                index -= 1
                return self.click_element(index, **kwargs)
            else:
                logger.exception(e)
                email_msg = dict(status=4041, subject='点击事件标签错误', content=f"页面未检测到该标签, 标签内容: {kwargs}")
                self.__flush_msg_queue__(
                    errorlevel=SpiderMessage.ErrorLevel.__dict__['Critical'], msg=f"{email_msg.get('subject')}, 等待人工处理",
                    sattus=400, data=email_msg, **SpiderMessage.LoginInitFailed.__dict__
                )
        except StaleElementReferenceException:
            self.driver.refresh()
            index -= 1
            return self.click_element(index, **kwargs)
        except ElementClickInterceptedException:
            # 元素存在, 但是不能点击
            self.__get_data_click_exception_tag__(**kwargs)
            # 元素存在, 但是不能点击, 尝试使用鼠标点击
            # actions = ActionChains(self.driver)
            # actions.click(element_obj).perform()
            pass
        except ElementNotInteractableException:
            self.__get_data_click_exception_tag__(**kwargs)
            # self.driver.refresh()
        except NoSuchElementException as e:
            #  Message: no such element: Unable to locate element:
            logger.warning(e.msg)
            self.__get_data_click_exception_tag__(**kwargs)
            # raise NoSuchElementException(e.msg)

    def get_page_source(self):
        """获取对象的源代码"""
        html = self.driver.page_source
        return html

    def skipping_send_page(self, send_tag, click_tag, page, **kwargs):
        """
        跳转到指定页面
        @param click_tag: 点击跳转的标签匹配值
        @param send_tag: 填入跳转页面的标签匹配值
        @param page: 跳转的页面
        @param kwargs:
        @return:
        """
        self.send_element(page, **send_tag)
        time.sleep(0.5)
        self.click_element(**click_tag)

    def send_element(self, content, **kwargs):
        """输入事件"""
        try:
            # 等待标签加载成功
            element = self.driver.find_element(**self.parse_element_condition(**kwargs))
            # 通过键盘全选, 然后清除值
            element.send_keys(Keys.CONTROL, 'a')
            element.send_keys(Keys.DELETE)
            # 输入数据
            element.send_keys(content)
        except ElementClickInterceptedException as e:
            logger.exception(e)
            email_msg = dict(status=4041, subject='输入事件标签错误', content=f"页面未检测到该标签, 标签内容: {kwargs}")
            self.__flush_msg_queue__(
                errorlevel=SpiderMessage.ErrorLevel.__dict__['Critical'], msg=f"{email_msg.get('subject')}, 等待人工处理",
                sattus=400, data=email_msg, **SpiderMessage.LoginInitFailed.__dict__
            )
            self.is_login_success_wait(**kwargs)

    def get_element_inner_text(self, index=5, **kwargs):
        """获取标签内的值事件"""
        if not self.block_waiting(**kwargs):
            raise ElementNotVisibleException()
        try:
            text = self.driver.find_element(**kwargs).get_attribute('innerText')
            return text
        except ElementClickInterceptedException as e:
            logger.exception(e)
            email_msg = dict(status=4041, subject='获取标签内容发生错误', content=f"页面未检测到该标签, 标签内容: {kwargs}")
            self.__flush_msg_queue__(
                errorlevel=SpiderMessage.ErrorLevel.__dict__['Critical'], msg=f"{email_msg.get('subject')}, 等待人工处理",
                sattus=400, data=email_msg, **SpiderMessage.LoginInitFailed.__dict__
            )
        return None

    def get_elements_inner_text(self, **kwargs):
        if not self.block_waiting(**kwargs):
            return None
        try:
            elements_obj_list = self.driver.find_elements(**kwargs)
            text_list = []
            for element in elements_obj_list:
                text_list.append(element.get_attribute('innerText'))
            return text_list
        except ElementClickInterceptedException as e:
            logger.exception(e)
            email_msg = dict(status=4041, subject='批量获取标签内容发生错误', content=f"页面未检测到该标签, 标签内容: {kwargs}")
            self.__flush_msg_queue__(
                errorlevel=SpiderMessage.ErrorLevel.__dict__['Critical'], msg=f"{email_msg.get('subject')}, 等待人工处理",
                sattus=400, data=email_msg, **SpiderMessage.LoginInitFailed.__dict__
            )
        except StaleElementReferenceException as e:
            logger.exception(e)
            self.driver.refresh()
            return self.get_elements_inner_text(**kwargs)
        return None

    def wrong_password(self, **kwargs):
        """检测是否密码错误"""
        text = ''
        for err_tag in self.wrongPassword:
            if self.is_element_exist(**err_tag):
                text += self.get_element_inner_text(
                    **self.parse_element_condition(**err_tag)
                )
        if text:
            self.__flush_msg_queue__(**dict(
                msg="登录失败, 账户密码错误", data=text, **SpiderMessage.LoginFailed.__dict__,
            ))
            return True
        return False

    def manual_work(self, orderId=None, **kwargs):
        """检测人工处理时的界面登录成功状态"""
        # 弃用
        timeout = self.timeout["timeoutManualWork"]
        while timeout:
            if self.block_waiting(**self.waitingTag['loginSuccess']):
                # 登录成功, 发送通知
                self.__flush_msg_queue__(
                    msg="登录成功, 开始采集", data=None, **SpiderMessage.LoginSuccess.__dict__
                )
                self._state_ = SpiderMessage.Status.LOGIN_SUCCESS
                return True
            else:
                timeout -= 5
                time.sleep(5)
        # 人工处理超时也未登录成功, 发送异常邮件
        email_msg = {**kwargs, **{"status": 4023, "subject": f"{self.user}-人工处理超时", "content": '人工处理超时,退出等待'}}
        self.__flush_msg_queue__(data=email_msg,
                                 errorlevel=SpiderMessage.ErrorLevel.__dict__['Critical'],
                                 msg=f"{email_msg.get('subject')}, 等待人工处理",
                                 **SpiderMessage.LoginExceptionManualWork.__dict__)
        return False

    def __send_account_pwd__(self, **kwargs):
        """输入账户密码"""
        if self._state_ >= SpiderMessage.Status.LOGIN_SUCCESS:
            # 此步骤已执行
            return True
        print('输入账户密码')
        # 等待登陆界面 子 页面加载成功
        self.block_waiting(**self.loginTag['childIframe'])
        # 1. 切换到登录子页面
        self.driver.switch_to.frame(self.loginTag['childIframe']['value'])
        # 2. 输入账户
        self.send_element(self.user, **self.loginTag['account'])
        # 3. 输入密码
        self.send_element(self.pwd, **self.loginTag['password'])
        time.sleep(0.5)
        # 4. 点击登录
        self.click_element(**self.loginTag['loginClick'])
        # 5. 检测是否登录成功
        if not self.is_login_success():
            return False
        self._state_ = SpiderMessage.Status.LOGIN_SUCCESS
        return True

    def __login_init__(self, **kwargs):
        """登录初始化"""
        # self.__start_webdriver__(**kwargs)
        # self.driver.get(self.LOGIN_URL)
        self.window_handle = self.driver.current_window_handle  # microsoft 的窗口句柄
        js = 'window.open("https://www.baidu.com/");'
        self.driver.execute_script(js)
        # 获取当前窗口句柄集合（列表类型）
        handles = self.driver.window_handles
        # 获取百度窗口句柄
        for handle in handles:
            if handle != self.window_handle:
                self.baidu_handle = handle
        self.driver.switch_to.window(self.window_handle)

    def is_login_success(self, **kwargs):
        """循环检测是否登录成功"""
        while True:
            # 检查登录成功标签
            if self.is_element_exist(**self.loginSuccess):
                print('登录成功')
                return True
            # 检测账户密码是否错误
            elif self.wrong_password(**kwargs):
                return False
            # 检测是否 出现认证二维码
            elif self._state_ != SpiderMessage.Status.LOGIN_VERIFY:
                for itemTag in self.loginExceptionTag:
                    if self.is_element_exist(**itemTag):
                        print('出现风控验证, 请处理....')
                        # input('出现风控验证, 认证成功后请输入回车继续执行程序')
                        # print('已收到命令, 开始继续执行程序')
                        # self.driver.refresh()
                        self._state_ = SpiderMessage.Status.LOGIN_VERIFY
            time.sleep(1)
            print('循环检测是否登录成功中...')

    def is_login_success_disposable(self, **kwargs):
        """用于一次性检测登陆是否成功, 主要用在登录成功后, 采集数据发生异常时"""
        if self.is_element_exist(**self.loginSuccess):
            self._state_ = SpiderMessage.Status.LOGIN_SUCCESS
            # 登录成功
            self.__flush_msg_queue__(**dict(
                msg="登录成功, 采集数据发生异常", data=None,
                **SpiderMessage.LoginSuccess.__dict__
            ))
            return True
        else:
            return False

    def __get_data_click_exception_tag__(self, **kwargs):
        """获取数据时, 点击异常, 检测异常原因的函数"""
        # 循环检测是否出现异常标签
        # time.sleep(5)
        # clickExceptionClickTag = copy.deepcopy(self.clickExceptionClickTag)
        for except_tag in self.getDataVerify:
            if self.is_element_exist(**except_tag):
                # 采集数据阶段出现二次验证码, 循环检测等待标签消失
                while True:
                    try:
                        self.block_not_waiting(**except_tag)
                    except:
                        pass
                    input('采集数据中出现二次风控验证, 认证成功后请输入回车继续执行程序....')
                    self._state_ = SpiderMessage.Status.COllECT_VERIFY
                    time.sleep(2)

        for except_tag in copy.deepcopy(self.clickExceptionClickTag):
            if self.is_element_exist(
                    **dict(by=except_tag['detection']['by'], value=except_tag['detection']['value'])):
                # 等待标签的不可操作disabled 属性消失
                self.block_not_waiting(**dict(by=except_tag['notarize']['by'],
                                              value='//button[@disabled]' + except_tag['notarize']['value']))
                # 等待标签加载成功
                if self.block_waiting(**dict(by=except_tag['notarize']['by'], value=except_tag['notarize']['value'])):
                    try:
                        self.driver.find_element(
                            **dict(by=except_tag['notarize']['by'], value=except_tag['notarize']['value'])).click()
                        self.clickExceptionClickTag.remove(except_tag)
                    except ElementClickInterceptedException as e:
                        logger.exception(e)
                        continue
            time.sleep(1)
            # time.sleep(1)
        # 删除 body 下第一个以外的 子级 div标签
        # elements = self.driver.find_elements(**self.parse_element_condition(**self.clickExceptionDeleteTag))
        # for element in elements:
        #     self.driver.execute_script("""
        #     var element = arguments[0];
        #     element.parentNode.removeChild(element);
        #     """, element)


if __name__ == '__main__':
    # user = 'ali088602014831:阿紫'
    # pwd = 'qiuyuan888'
    user = '个性臭臭:小法'
    pwd = 'dingding888'
    data = config['qianNiu']
    BaseWebDriver(**{
        **dict(
            user=user,
            pwd=pwd,
        ),
        **data
    }).run()
