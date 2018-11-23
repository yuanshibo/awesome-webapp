#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# __author__ = 'Y'

# '''
# async web application.
# '''


# asyncio的编程模型就是一个消息循环，通过async关键字定义一个协程（coroutine），协程也是一种对象。
# 协程不能直接运行，需要把协程加入到事件循环（loop），由后者在适当的时候调用协程。
# asyncio.get_event_loop方法可以创建一个事件循环，然后使用run_until_complete将协程注册到事件循环，并启动事件循环。

import asyncio, os, json, time
from datetime import datetime

from aiohttp import web

#logging 日志
# 在logging.basicConfig()函数中可通过具体参数来更改logging模块默认行为，可用参数有：
# 　　filename：用指定的文件名创建FiledHandler（后边会具体讲解handler的概念），这样日志会被存储在指定的文件中。
# 　　filemode：文件打开方式，在指定了filename时使用这个参数，默认值为“a”还可指定为“w”。
# 　　format：指定handler使用的日志显示格式。
# 　　datefmt：指定日期时间格式。
# 　　level：设置rootlogger（后边会讲解具体概念）的日志级别
# 　　stream：用指定的stream创建StreamHandler。可以指定输出到sys.stderr,sys.stdout或者文件，默认为sys.stderr。若同时列出了filename和stream两个参数，则stream参数会被忽略。
# 　　format参数中可能用到的格式化串：
# 　　%(name)s Logger的名字
# 　　%(levelno)s 数字形式的日志级别
# 　　%(levelname)s 文本形式的日志级别
# 　　%(pathname)s 调用日志输出函数的模块的完整路径名，可能没有
# 　　%(filename)s 调用日志输出函数的模块的文件名
# 　　%(module)s 调用日志输出函数的模块名
# 　　%(funcName)s 调用日志输出函数的函数名
# 　　%(lineno)d 调用日志输出函数的语句所在的代码行
# 　　%(created)f 当前时间，用UNIX标准的表示时间的浮 点数表示
# 　　%(relativeCreated)d 输出日志信息时的，自Logger创建以 来的毫秒数
# 　　%(asctime)s 字符串形式的当前时间。默认格式是 “2003-07-08 16:49:45,896”。逗号后面的是毫秒
# 　　%(thread)d 线程ID。可能没有
# 　　%(threadName)s 线程名。可能没有
# 　　%(process)d 进程ID。可能没有
# 　　%(message)s用户输出的消息
import logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename='webapp.log',
                    filemode='w')
"""
level=logging.DEBUG:修改默认输出级别为Debug
format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s'：指定handler使用的日志显示格式。
    %(asctime)s：字符串形式的当前时间
    %(filename)s：调用日志输出函数的模块的文件名
    [line:%(lineno)d]：调用日志输出函数的语句所在的代码行
    %(levelname)s：文本形式的日志级别
    %(message)s：用户输出的消息
datefmt='%a, %d %b %Y %H:%M:%S'：设置日期格式
    %a:星期
    %d:日期
    %b:月份
    %Y:年
    %H:%M:%S：时：分：秒
filename='test.log'：设置日志输出文件
filemode='w'：设置日志输出文件打开方式
"""
logging.debug('debug message')
logging.info('info message')
logging.warning('warning message')
logging.error('error message')
logging.critical('critical message')

"""
test.log文件内容：
Wed, 21 Jun 2017 16:54:30 test.py[line:12] DEBUG debug message
Wed, 21 Jun 2017 16:54:30 test.py[line:13] INFO info message
Wed, 21 Jun 2017 16:54:30 test.py[line:14] WARNING warning message
Wed, 21 Jun 2017 16:54:30 test.py[line:15] ERROR error message
Wed, 21 Jun 2017 16:54:30 test.py[line:16] CRITICAL critical message

"""

async def index(request):
    """响应函数"""
    return web.Response(body=b'<h1>Awesome</h1>',content_type='text/html')

async def hello(request):
    text = '<h1>hello, %s!</h1>' % request.match_info['name']
    return web.Response(body=text.encode('utf-8'),content_type='text/html')

async def init(loop):
    # 制作响应合集
    app = web.Application(loop=loop)
    # 把响应函数添加到响应函数集合
    app.router.add_route(method='GET', path='/', handler=index)
    app.router.add_route(method='GET', path='/hello/{name}', handler=hello)
    # 创建服务器（连接网址、端口，绑定handler）
    srv = await loop.create_server(app.make_handler(), '127.0.0.1', 9000)
    logging.info('server started at http://127.0.0.1:9000...')
    return srv

# 创建事件
loop = asyncio.get_event_loop()
# 运行
loop.run_until_complete(init(loop))
# 服务器不关闭
loop.run_forever()