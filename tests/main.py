import unittest
import sys
import os
import logging

logging.basicConfig(level=logging.INFO,
                    filename='logs/tests.log',
                    filemode='w',
                    format='{levelname:<8} {name:<15} {message}',
                    style='{')

# only use absoute imports. The dirname of the current script is always added
# to sys.path, which I don't want. I just want the root directory of the
# project, and I import from there
for i, path in enumerate(sys.path):
    if path == os.path.dirname(os.path.abspath(__file__)):
        sys.path[i] = os.getcwd()

from tests.connection import TestConnection
from tests.server import TestServer

SLOW_TEST_THRESHOLD = 0.3

def average(*nums):
    return sum(nums) / len(nums)

if __name__ == '__main__':
    try:
        unittest.main(exit=False)
        pass
    except KeyboardInterrupt as e:
        pass

    print()

    # display slow tests
    times = TestServer.get_times()

    setup = round(average(*times['setup']), 2)
    teardown = round(average(*times['teardown']), 2)
    print(f" SLOW TEST TIMES ({setup}, {teardown}) ".center(70, '='))
    print()

    for name, time in times['tests'].items():
        if time < SLOW_TEST_THRESHOLD:
            continue
        print(f"{name.rjust(20)} -> {round(time, 2)}s")
    # display the logs
    print()
    print(' LOGS '.center(70, '='), '\n', flush=True)
    with open('logs/tests.log', 'r') as fp:
        print(fp.read())
