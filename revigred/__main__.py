if __name__ == '__main__' and __package__ is None:
    import sys, os
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, parent_dir)
    __package__ = str("revigred")
    del sys, os


import sys
import asyncio
from datetime import datetime

from metaconfig import Config

from revigred.reloader import run_with_reloader
from revigred.protocol import ServerFactory
from revigred.model import Chat
from revigred.utils import title

def parse_args():
    import argparse

    parser = argparse.ArgumentParser(
        description='',
        )
    
    parser.add_argument('-c', '--config', 
        dest='config', help='path to config file (should be yaml)')

    return parser.parse_args()

def main():

    print(title(str(datetime.now())))

    args = parse_args()

    config = Config()
    config.load(args.config)

    server = config.get_dependency("server")
    host = server.host
    port = server.port
    logger = server.logging.logger
    handler = server.logging.handler

    with handler.applicationbound():
        logger.info("Starting server at http://{}:{}".format(host, port))

        loop = asyncio.get_event_loop()

        ws_url = "ws://{}:{}".format(host, port)
        factory = ServerFactory(ws_url, 
            loop=loop, model=server.model, logger=logger, debug=False)

        coro = loop.create_server(factory, host, port)
        server = loop.run_until_complete(coro)

        try:
            loop.run_forever()
        except KeyboardInterrupt:
            sys.exit(0)
        else:
            sys.exit(3)
        finally:
            server.close()
            loop.close()
            print("Stopping server.")

if __name__ == '__main__':
    run_with_reloader(main)
