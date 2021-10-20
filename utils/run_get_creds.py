if __name__ == "__main__":
    import asyncio
    import os
    import sys
    p = os.path.abspath('.')
    sys.path.insert(1, p)
    from database import MongoDB
    mongodb = MongoDB()
    from GoogleSpreadsheetsAPI import get_creds
    asyncio.run(get_creds.get_creds(mongodb))