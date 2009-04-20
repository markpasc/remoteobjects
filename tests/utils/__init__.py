import functools
import httplib2
import logging
import os

import mox
import nose

def skip(fn):
    def testNothing(self):
        raise nose.SkipTest('skip this test')
    functools.update_wrapper(testNothing, fn)
    return testNothing

def are_automated():
    return bool(os.getenv('AUTOMATED_TESTING'))

def skip_if_automated(fn):
    if are_automated():
        return skip(fn)
    return fn

def todo(fn):
    def testReverse(*args, **kwargs):
        try:
            fn(*args, **kwargs)
        except:
            pass
        else:
            raise AssertionError('test %s unexpectedly succeeded' % fn.__name__)
    functools.update_wrapper(testReverse, fn)
    return testReverse

class MockedHttp(object):
    def __init__(self, req, resp_or_content):
        self.mock = mox.MockObject(httplib2.Http)

        if not isinstance(req, dict):
            req = dict(uri=req)

        resp, content = self.make_response(resp_or_content, req['uri'])
        self.mock.request(**req).AndReturn((resp, content))

    def make_response(self, response, url):
        default_response = {
            'status':           200,
            'etag':             '7',
            'content-type':     'application/json',
            'content-location': url,
        }

        if isinstance(response, dict):
            if 'content' in response:
                content = response['content']
                del response['content']
            else:
                content = ''

            status = response.get('status', 200)
            if 200 <= status < 300:
                response_info = dict(default_response)
                response_info.update(response)
            else:
                # Homg all bets are off!! Use specified headers only.
                response_info = dict(response)
        else:
            response_info = dict(default_response)
            content = response

        return httplib2.Response(response_info), content

    def __enter__(self):
        mox.Replay(self.mock)
        return self.mock

    def __exit__(self, *exc_info):
        # don't really care about the mock if there was an exception
        if None in exc_info:
            mox.Verify(self.mock)

def log():
    import sys
    logging.basicConfig(level=logging.DEBUG, stream=sys.stderr, format="%(asctime)s %(levelname)s %(message)s")