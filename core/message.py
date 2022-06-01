# -*- coding: UTF-8 -*-


class SpiderMessageCode:

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            object.__setattr__(self, k, v)
        pass

    def __setattr__(self, key, value):
        object.__setattr__(self, key, value)

    def __getattr__(self, item):
        return self.__dict__.get(item, None)

    def __eq__(self, other):
        return self.code == other


MessageProtocol = {
    "StartBrowser": 000,  # 启动浏览器, 开始任务
    "LoginTypeChoose": 100,  # 支持的登录方式
    "LoginTypeConfirm": 101,  # 确认登录方式
    "LoginTypeDetails": 102,  # 登录要素
    "LoginInfoGetMobileVerifyCode": 1021,  # 获取短信验证码
    "LoginInfoPutMobileVerifyCode": 1022,  # 返回短信验证码
    "SubmitLoginArgs": 103,  # 提交登录参数
    "LoginSuccess": 201,  # 登录成功
    "LoginInitFailed": 400,  # 登录首页打开失败
    "LoginFailed": 401,  # 登录失败
    "StartBrowserError": 500,  # 启动浏览器失败
}


class SpiderMessage:
    # 登录时可能出现的输入要素：
    args = (
        'USERNAME',  # 用户名，也可以是邮箱号、手机号
        'PASSWORD',  # 用户密码
        'IMG_VERIFY_CODE',  # 图形验证码
        'MOBILE_PHONE',  # 手机号码
        'MOBILE_VERIFY_CODE',  # 手机验证码
        'QR_CODE',  # 二维码
    )

    LoginInitFailed = SpiderMessageCode(**{
        'code': 401,
        'type': 'LoginInitFailed',
        # 'msg': '登录页面打开失败，请联系管理员'
    })
    StartBrowser = SpiderMessageCode(**{
        'code': 000,
        'type': 'StartBrowser',
        'msg': '启动浏览器, 并准备登录'
    })
    LoginTypeChoose = SpiderMessageCode(**{
        'code': 100,
        'type': 'LoginTypeChoose',
        # 'msg': '选择合适的登录方式',
        # 'data': [
        #     {
        #         'type': 1,
        #         'args': ['USERNAME', 'PASSWORD', 'IMG_VERIFY_CODE'],
        #         'img_verify_code_url': 'http://ip:port/syx/data/scrapy/img-verify-code/{$orderId}'
        #     },  # 账号+密码+图形验证码，默认
        #     {'type': 2, 'args': None},  # 手机号码+手机短信验证码
        #     {'type': 2, 'args': None},  # 二维码
        # ]
    })

    LoginTypeConfirm = SpiderMessageCode(**{
        'code': 101,
        'type': 'LoginTypeConfirm',
        # 'msg': '确认登录方式',
        # 'data': {
        #     'type': 2
        # }
    })
    LoginInfoMobilePhone = SpiderMessageCode(**{
        'code': 1020,
        'type': 'LoginInfoMobilePhone',
        # 'msg': '确认登录的手机号',
        # 'data': {
        #         'orderId': 1,
        #         'platform':'美团优选'
        #         'type': 2,
        #         'args': ['MOBILE_PHONE', 'MOBILE_VERIFY_CODE'],
        #         'data':{'MOBILE_PHONE':'12345678912'}
        # }# args的值根据登录方式的不同，返回不同的值这里只是举例
    })

    LoginTypeDetails = SpiderMessageCode(**{
        'code': 102,
        'type': 'LoginTypeDetails',
        # 'msg': '填写登录信息',
        # 'data': {
        #     'type': 2,
        #     'args': ['MOBILE_PHONE', 'MOBILE_VERIFY_CODE']
        # }
    })
    LoginExceptionManualWork = SpiderMessageCode(**{
        'code': 4010,
        'type': 'LoginExceptionManualWork',
        # 'msg': '登录异常需要人工处理',
        # 'data': {
        #     "status": "{异常类型}",
        #     "result": {
        #         "args": {
        #             "subject": "{orderId}登录出现异常",
        #             "content": "{异常原因}",
        #             "receivers": ["{接收者邮箱}"],
        #             "cc": None
        #         },
        #     },
        #     "date_done": "{异常发生时间}"
        # }
    })

    LoginInfoGetMobileVerifyCode = SpiderMessageCode(**{
        'code': 1020,
        'type': 'LoginInfoGetMobileVerifyCode',
        # 'msg': '获取短信验证码',
        # 'data': {
        #     'mobile_phone': '15800130013',
        #     # 'img_verify_code': '1234',    # 如果获取短信验证码也要填图形验证码的话
        # }
    })

    LoginInfoPutMobileVerifyCode = SpiderMessageCode(**{
        'code': 1023,
        'type': 'LoginInfoPutMobileVerifyCode',
        # 'msg': '返回的短信验证码',
        # 'data': {
        #     'mobile_phone': '15800130013',
        #     'mobile_verify_code': '0391',
        # }
    })

    SubmitLoginArgs = SpiderMessageCode(**{
        'code': 103,
        'type': 'SubmitLoginArgs',
        # 'msg': '提交登录参数',
        # 'data': {
        #     'type': 1,
        #     'args': ['USERNAME', 'PASSWORD'],
        #     'values': ['user1', '12345']
        # }
    })
    LoginQRCodePath = SpiderMessageCode(**{
        'code': 104,
        'type': 'LoginQRCodePath',
        # 'msg': '扫码登录地址',
        # 'data': {
        #   'orderId': 1,
        #   'status':200,
        #   'qr_code_file_path':'二维码路径地址',
        # }
    })

    LoginFailed = SpiderMessageCode(**{
        'code': 401,
        'type': 'LoginFailed',
        # 'msg': '登录失败(账号密码错误)'
    })

    LoginSuccess = SpiderMessageCode(**{
        'code': 201,
        'type': 'LoginSuccess',
        # 'msg': '登录成功'
    })

    # 采集完成, 会话结束
    Finish = SpiderMessageCode(**{
        'code': 888,
        'type': 'Finish',
        'msg': '处理完成，会话结束'
    })

    # 启动浏览器失败
    StartBrowserError = SpiderMessageCode(**{
        'code': 500,
    })

    SpiderSchedule = SpiderMessageCode(**{
        'code': 202,
        # 'msg': '采集进度',
        # "data": {
        #     'orderId': 1,
        #     'msg': '正在采集',
        #     'modules': TiktokShopBasicInfo,
        #     'quantity': '{采集完成条数}/{总条数}',
        #     'pages': '采集页面/总页面',
        # }
    })

    # 登录 获取数据执行路径
    Status = SpiderMessageCode(**{
        "INIT": 0,  # 初始化阶段
        "READY": 1,  # 准备阶段
        "LOGIN": 2,  # 登录阶段
        "LOGIN_VERIFY": 3,  # 登录出现验证码阶段
        "LOGIN_SUCCESS": 4,  # 登录成功阶段
        "COLLECT": 5,  # 采集数据阶段
        "COllECT_VERIFY": 6,  # 采集数据出现验证码阶段
        "MANUAL": 7,  # 人工干预中
        "FINISH": 8,  # 完成
    })

    # 采集步骤
    QNSpiderPoint = SpiderMessageCode(**{
        "START": 0,  # 开始采集阶段
        "LATELY_TRIMESTER": 1,  # 采集完成最近三个月的订单
        "LATELY_TRIMESTER_EXCEPT": 2,  # 采集完成最近三个月以外的订单
        "SHOP_FINISH": 200,  # 采集完成
    })

    LoginTypes = SpiderMessageCode(**{
        "USERNAME_PASSWORD": 1,
        "MOBILE_PHONE_VERIFY_CODE": 2,
        "QR_CODE": 3,
        "USERNAME_PASSWORD_IMG_VERIFY_CODE": 4,
        "DOU_DIAN_APP": 31,
        "DOU_YIN_APP": 32,
        "TOU_TIAO_APP": 33,
        "HUO_SHAN_APP": 34,
    })

    ErrorLevel = SpiderMessageCode(**{
        "General": 1,
        "Critical": 2
    })


print(SpiderMessage.Status.__dict__)
