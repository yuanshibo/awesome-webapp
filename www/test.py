
#データ登録
import orm
import asyncio
from models import User, Blog, Comment
import random

async def Users(loop):
    await orm.create_pool(loop=loop, user='www-data', password='www-data', db='awesome')
    u = User(name='Test', email='lxp@exa22mple.com', passwd='1234567890', image='about:blank')
    u =User(name='test',email='test%s@example.com' % random.randint(0,10000000),admin =True,passwd='abc123456',image='about:blank')
    await u.save()

async def Blogs(loop):
    await orm.create_pool(loop=loop, user='www-data', password='www-data', db='awesome')
    u = Blog(name='Test', email='lxp@exa22mple.com', passwd='1234567890', image='about:blank')
    u =Blog(name='test',email='test%s@example.com' % random.randint(0,10000000),admin =True,passwd='abc123456',image='about:blank')
    await u.save()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(Blogs(loop))
loop.close()