from uvicorn.workers import UvicornWorker


class MyUvicornWorker(UvicornWorker):
	# CONFIG_KWARGS = {"loop": "auto", "http": "auto"}
	CONFIG_KWARGS = {
		"loop": "uvloop",
        "http": "httptools",
	}
