from MyLogger import Logger
logging = Logger().logging


def on_starting(server):
    """
    Called just before the master process is initialized.
    """
    logging.info("Server is starting")


def when_ready(server):
    """
    Called just after the server is started.
    """
    logging.info("Server has started")


def on_reload(server):
    """
     Do something on reload
    """
    logging.info("Server has reloaded")


def post_worker_init(worker):
    """
    Do something on worker initialization
    """
    print(worker)
    
    logging.info(f"Worker has been initialized. Worker Process id –> {worker.pid}")
