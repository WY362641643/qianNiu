#!/usr/bin/env python3
# -*- coding: utf-8 -*-

config = {
    'qianNiu': {
        # 所有的链接存放地址
        'linkAll': {
            # 登陆地址
            'loginUrl': 'https://myseller.taobao.com/home.htm/QnworkbenchHome/',
            # 已卖出宝贝的地址
            'outGoods': 'https://myseller.taobao.com/home.htm/trade-platform/tp/sold',
            # 新页面获取数据
            'getDataUrl': 'https://trade.taobao.com/trade/detail/trade_order_detail_qian_niu.htm?bizOrderId={orderId}&sifg=1&isQnNew=true',
            # 旧页面获取数据
            'getDataUrlFormer': 'https://tradearchive.taobao.com/trade/detail/trade_item_detail.htm?biz_order_id={orderId}&sifg=1',
        },
        # 页面最大刷新次数
        'pageRefreshMax': 20,
        # 浏览器启动器路径
        'driverPath': 'core/chromedriver.exe',
        # 最近三个月已经采集过的页码数
        'paging_trimester': 0,
        # 最近三个月以外已经采集过的页码数
        'paging_trimester_except': 0,
        # 设置redis队列中 最大 订单号存储量
        'push_number':50,
        # 不采集的订单状态, 包含
        'includeNoSpiderOrderStatus': '(交易成功)|(卖家已发货)',
        # 设置超时
        'timeout': {
            'webDriverTimeout': 5,
        },
        # 登录页面的标签
        'loginTag': {
            # 登录界面打开成功监听的标签
            'getLoginSuccess': {'by': 'id', 'value': 'alibaba-login-iframe'},
            # 登录子页面
            'childIframe': {'by': 'id', 'value': 'alibaba-login-box'},
            # 账户标签
            'account': {'by': 'xpath', 'value': '//input[@placeholder="账号名/邮箱/手机号"]'},
            # 密码标签
            'password': {'by': 'xpath', 'value': '//input[@placeholder="请输入登录密码"]'},
            # 点击登录标签
            'loginClick': {'by': 'xpath', 'value': '//button[text()="登录"]'},
            # 出现认证二维码, 认证成功后刷新页面后出现的标签 --> 下次再说
            'nextTalkClick': {'by': 'xpath', 'value': '//button[text()="下次再说"]'},
        },
        # 登录成功标签
        'loginSuccess': {'by': 'id', 'value': 'icestark-container'},
        # 账户密码错误组
        'wrongPassword': [{'by': 'xpath', 'value': '//div[text()="账号名或登录密码不正确"]'}],

        # 登陆失败的标签组
        'loginExceptionTag': [
            # 出现认证二维码 --> 特别注意：每个子账号的二维码不同，请直接扫描本页面上的最新二维码
            {'by': 'xpath', 'value': '//p[text()="特别注意：每个子账号的二维码不同，请直接扫描本页面上的最新二维码"]'},
            # 认证成功！请您重新登录！
            {'by': 'xpath', 'value': '//p[text()="认证成功！请您重新登录！"]'},
            # 手机校验码
            {'by': 'xpath', 'value': '//button[text()="点击获取验证码"]'},
            # 获取短信校验码
            {'by': 'xpath', 'value': '//button[text()="获取短信校验码"]'},
            # 通过验证以确保正常访问
            {'by': 'xpath', 'value': '//p[text()="通过验证以确保正常访问"]'},
        ],
        # 采集数据的点击标签
        'getDataClickTag': {
            # 等待数据加载成功标签
            'dataShow': {'by': 'xpath', 'value': '//div[text()="订单号："]'},
            # 等待数据加载成功, 有数据或者无数据都可以检测
            'dataShowInfo': {'by': 'xpath',
                             'value': '//div[@class="next-table-empty" or @class="next-table-row first"]'},
            # 点击左侧商品栏目
            'clickCommodity': {'by': 'xpath', 'value': '//span[text()="交易"]'},
            # 点击已卖出的宝贝
            'clickSold': {'by': 'xpath', 'value': '//a[text()="已卖出的宝贝"]'},
            # 点击代发货
            'clicPending': {'by': 'xpath', 'value': '//div[text()="待发货"]'},
            # 点击最近三个月
            'clickLatelyTrimester': {'by': 'xpath', 'value': '//div[text()="近三个月订单"]'},
            # 点击三个月前
            'clickLatelyTrimesterExcept': {'by': 'xpath', 'value': '//div[text()="三个月前订单"]'},
            # 点击下一页
            'click_next_page': {'by': 'xpath', 'value': '//span[text()="下一页"]/parent::button'},
            # 更多页面,
            'morePages': {'by': 'xpath',
                          'value': '''//span[text()="显示更多页码"]/parent::button[contains(@style,'display: block;')]'''},
            # 直接到达指定页面的输入标签
            'send_arriver_paging': {'by': 'xpath', 'value': '//input[@aria-label="请输入跳转到第几页"]'},
            # 直接到达指定页面的确认标签  获取最后一个 button标签
            'click_arriver_paging': {'by': 'xpath', 'value': '//span[text()="确定"]/parent::button'},

        },
        # 采集数据的加载中标签组
        'getDataTagDoing': {
            # 点击下一页的加载标签
            'next_page_loading': {'by': 'xpath', 'value': '//div[contains(@class,"next-loading")]'}
        },
        # 采集数据的标签组
        'getDataTag': {
            # 获取当前页码
            'get_paging': {'by': 'xpath', 'value': '//button[contains(@class,"next-current")]'},
            # 当前所有可以点击的页码
            'pages_tag': {'by': 'xpath', 'value': '//span[text()="下一页"]/parent::button/parent::div/div'},
            # 获取订单状态
            'orderStatus': {'by': 'xpath', 'value': '//td[@data-next-table-col="5"]/div/div[1]/div[1]'},
            # 获取订单页面的价格
            'orderPrice': {'by': 'xpath', 'value': '//td[@data-next-table-col="6"]/div/div/div[1]'},
            # 获取订单数量
            'orderNumber': {'by': 'xpath', 'value': '//td[@data-next-table-col="3"]/div/div'},

        },
        # 登录成功 采集数据阶段, 点击异常, 需要处理的悬浮标签
        'clickExceptionClickTag': [
            {'detection': {'by': 'xpath', 'value': '//div[text()="千牛工作台升级说明"]'},
             'notarize': {'by': 'xpath', 'value': '//div[text()="跳过"]'}},
            {'detection': {'by': 'xpath', 'value': '//div[text()="这里可以搜索常用的菜单，快速找到你经常使用的功能"]'},
             'notarize': {'by': 'xpath', 'value': '//div[text()="跳过"]'}},
        ],
        # 登录成功, 采集数据时需要进行的二次验证
        'getDataVerify': [
            {'by': 'xpath', 'value': '//div[text()="请输入6位数字验证码："]'},
            {'by': 'xpath', 'value': '//input[@value="免费获取验证码"]'},
            {'by': 'xpath', 'value': '//input[@placeholder="请输入6位数字验证码"]'}
        ],
        'headers': {
            'accept': 'application/json, text/plain, */*',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'origin': 'https://myseller.taobao.com',
            'referer': 'https://myseller.taobao.com/',
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="101", "Microsoft Edge";v="101"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36',
        },
        # 旧界面, 淘宝界面xpath匹配
        'taobao_page_data_xpath': {
            # 商品总价
            'price_all': {'by': 'xpath', 'value': '//td[@class="order-price"]'},
            # 运费
            'price_freight': {'by': 'xpath', 'value': '//td[@class="post-fee"]'},
        }

    }
}
# 登录地址
