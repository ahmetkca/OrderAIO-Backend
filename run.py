import uvicorn

if __name__ == '__main__':
    uvicorn.run("main:app",
                host="localhost",
                port=8000,
                reload=True,
                ssl_keyfile="./localhost.key",
                ssl_certfile="./localhost.crt")
