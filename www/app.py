#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# '''
# async web application.
# '''


# asyncio的编程模型就是一个消息循环，通过async关键字定义一个协程（coroutine），协程也是一种对象。
# 协程不能直接运行，需要把协程加入到事件循环（loop），由后者在适当的时候调用协程。
# asyncio.get_event_loop方法可以创建一个事件循环，然后使用run_until_complete将协程注册到事件循环，并启动事件循环。

import asyncio, os, json, time
from datetime import datetime

from aiohttp import web
from jinja2 import Environment, FileSystemLoader

from config import configs

import orm
from coroweb import add_routes, add_static

from handlers import cookie2user, COOKIE_NAME

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

def init_jinja2(app, **kw):
    logging.info('init jinja2...')
    options = dict(
        autoescape = kw.get('autoescape', True),
        block_start_string = kw.get('block_start_string', '{%'),
        block_end_string = kw.get('block_end_string', '%}'),
        variable_start_string = kw.get('variable_start_string', '{{'),
        variable_end_string = kw.get('variable_end_string', '}}'),
        auto_reload = kw.get('auto_reload', True)
    )
    path = kw.get('path', None)
    if path is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    logging.info('set jinja2 template path: %s' % path)
    env = Environment(loader=FileSystemLoader(path), **options)
    filters = kw.get('filters', None)
    if filters is not None:
        for name, f in filters.items():
            env.filters[name] = f
    app['__templating__'] = env

async def logger_factory(app, handler):
    async def logger(request):
        logging.info('Request: %s %s' % (request.method, request.path))
        # await asyncio.sleep(0.3)
        return (await handler(request))
    return logger

async def auth_factory(app, handler):
    async def auth(request):
        logging.info('check user: %s %s' % (request.method, request.path))
        request.__user__ = None
        cookie_str = request.cookies.get(COOKIE_NAME)
        if cookie_str:
            user = await cookie2user(cookie_str)
            if user:
                logging.info('set current user: %s' % user.email)
                request.__user__ = user
        if request.path.startswith('/manage/') and (request.__user__ is None or not request.__user__.admin):
            return web.HTTPFound('/signin')
        return (await handler(request))
    return auth

async def data_factory(app, handler):
    async def parse_data(request):
        if request.method == 'POST':
            if request.content_type.startswith('application/json'):
                request.__data__ = await request.json()
                logging.info('request json: %s' % str(request.__data__))
            elif request.content_type.startswith('application/x-www-form-urlencoded'):
                request.__data__ = await request.post()
                logging.info('request form: %s' % str(request.__data__))
        return (await handler(request))
    return parse_data

async def response_factory(app, handler):
    async def response(request):
        logging.info('Response handler...')
        r = await handler(request)
        if isinstance(r, web.StreamResponse):
            return r
        if isinstance(r, bytes):
            resp = web.Response(body=r)
            resp.content_type = 'application/octet-stream'
            return resp
        if isinstance(r, str):
            if r.startswith('redirect:'):
                return web.HTTPFound(r[9:])
            resp = web.Response(body=r.encode('utf-8'))
            resp.content_type = 'text/html;charset=utf-8'
            return resp
        if isinstance(r, dict):
            template = r.get('__template__')
            if template is None:
                resp = web.Response(body=json.dumps(r, ensure_ascii=False, default=lambda o: o.__dict__).encode('utf-8'))
                resp.content_type = 'application/json;charset=utf-8'
                return resp
            else:
                r['__user__'] = request.__user__
                resp = web.Response(body=app['__templating__'].get_template(template).render(**r).encode('utf-8'))
                resp.content_type = 'text/html;charset=utf-8'
                return resp
        if isinstance(r, int) and t >= 100 and t < 600:
            return web.Response(t)
        if isinstance(r, tuple) and len(r) == 2:
            t, m = r
            if isinstance(t, int) and t >= 100 and t < 600:
                return web.Response(t, str(m))
        # default:
        resp = web.Response(body=str(r).encode('utf-8'))
        resp.content_type = 'text/plain;charset=utf-8'
        return resp
    return response

def datetime_filter(t):
    delta = int(time.time() - t)
    if delta < 60:
        return u'1分钟前'
    if delta < 3600:
        return u'%s分钟前' % (delta // 60)
    if delta < 86400:
        return u'%s小时前' % (delta // 3600)
    if delta < 604800:
        return u'%s天前' % (delta // 86400)
    dt = datetime.fromtimestamp(t)
    return u'%s年%s月%s日' % (dt.year, dt.month, dt.day)

async def init(loop):
    await orm.create_pool(loop=loop, **configs.db)
    app = web.Application(loop=loop, middlewares=[
        logger_factory, auth_factory, response_factory
    ])
    init_jinja2(app, filters=dict(datetime=datetime_filter))
    add_routes(app, 'handlers')
    add_static(app)
    srv = await loop.create_server(app.make_handler(), '127.0.0.1', 9000)
    logging.info('server started at http://127.0.0.1:9000...')
    return srv

loop = asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()