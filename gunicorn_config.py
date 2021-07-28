from MyScheduler import MyScheduler
from database import MongoDB, MyRedis
from config import SCHEDULED_JOB_INTERVAL
from EtsyShopManager import EtsyShopManager
import asyncio


async def register_shop_jobs():
    mongodb = MongoDB()
    r = MyRedis().r
    myScheduler = MyScheduler()
    myScheduler.scheduler.start()
    etsy_connections = await mongodb.db["EtsyShopConnections"].find().to_list(100)
    job_offset = 0
    for etsy_connection in etsy_connections:
        _id = str(etsy_connection["_id"])
        myScheduler.scheduler.add_job(
            EtsyShopManager.syncShop,
            "interval",
            minutes=SCHEDULED_JOB_INTERVAL + job_offset,
            kwargs={"etsy_connection_id": _id,
                    "db": mongodb.db,
                    "r": r},
            id=f"{_id}:syncShopProcess",
            name=f"{_id}:syncShopProcess",
            # jobstore="mongodb"
        )
        job_offset += 5
    myScheduler.scheduler.print_jobs()


def on_starting(server):
    """
    Do something on server start
    """
    print("Server has started")
    print("Gunicorn on_starting event is working................")
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(register_shop_jobs())
    except Exception:
        pass


def on_reload(server):
    """
     Do something on reload
    """
    print("Server has reloaded")


def post_worker_init(worker):
    """
    Do something on worker initialization
    """
    print("Worker has been initialized. Worker Process id –>", worker.pid)