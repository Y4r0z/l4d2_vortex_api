from celery import Celery
import src.settings as settings
from src.api.tools import getRedis
import datetime
import redis
import logging

celery = Celery(__name__)
celery.conf.broker_url = settings.CELERY_BROKER_URL
celery.conf.result_backend = settings.CELERY_RESULT_BACKEND

redis_pool = redis.ConnectionPool.from_url(settings.REDIS_CONNECT_STRING, db=1)

@celery.on_after_configure.connect
def setup_periodic_tasks(sender: Celery, **kwargs):
    ...
    # sender.add_periodic_task(5.0, print_test.s(), name='print_test')




# @celery.task
# def print_test():
#     with redis.Redis(connection_pool=redis_pool) as r:
#         r.set('celery_test', datetime.datetime.now().isoformat())
#     logging.info('Redis SET TEST LOG')