def on_starting(server):
    """
    Do something on server start
    """
    print("Server has started")
    print("Gunicorn on_starting event is working................")


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
