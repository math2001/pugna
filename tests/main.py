import unittest
import sys
import os
import logging

logging.basicConfig(level=logging.DEBUG,
                    filename='tests.log',
                    filemode='w',
                    format='{asctime} {levelname:<5} {name:<15} {message}',
                    style='{')

# only use absoute imports. The dirname of the current script is always added
# to sys.path, which I don't want. I just want the root directory of the project,
# and I import from there

for i, path in enumerate(sys.path):
    if path == os.path.dirname(os.path.abspath(__file__)):
        sys.path[i] = os.getcwd()

from tests.connection import TestConnection
from tests.server import TestServer

if __name__ == '__main__':
    unittest.main(exit=False)
    print("\n" + "=" * 70, '\n', flush=True)
    with open('tests.log', 'r') as fp:
        print(fp.read(), flush=True)
