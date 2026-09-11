import functools
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from a2s.report_server import ReportHandler


class QuietHandler(ReportHandler):
    def log_message(self, *args):
        pass


class ReportServerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.payload = bytes(range(256)) * 1024
        Path(cls.temp.name, 'sample.mp4').write_bytes(cls.payload)
        handler = functools.partial(QuietHandler, directory=cls.temp.name)
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), handler)
        cls.worker = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.worker.start()
        cls.url = 'http://127.0.0.1:{}/sample.mp4'.format(cls.server.server_port)
        cls.client = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.worker.join()
        cls.temp.cleanup()

    def request(self, headers=None, method='GET'):
        return self.client.open(urllib.request.Request(self.url, headers=headers or {}, method=method))

    def test_full_and_head(self):
        with self.request() as r:
            self.assertEqual(r.status, 200)
            self.assertEqual(r.headers['Accept-Ranges'], 'bytes')
            self.assertEqual(r.read(), self.payload)
        with self.request(method='HEAD') as r:
            self.assertEqual(int(r.headers['Content-Length']), len(self.payload))
            self.assertEqual(r.read(), b'')

    def test_seeking_ranges(self):
        cases = [('bytes=65539-65700', 65539, 65700),
                 ('bytes=260000-', 260000, len(self.payload)-1),
                 ('bytes=-17', len(self.payload)-17, len(self.payload)-1),
                 ('bytes=262140-999999', 262140, len(self.payload)-1)]
        for value, start, end in cases:
            with self.subTest(value=value), self.request({'Range': value}) as r:
                self.assertEqual(r.status, 206)
                self.assertEqual(r.headers['Content-Range'], 'bytes {}-{}/{}'.format(start, end, len(self.payload)))
                self.assertEqual(r.read(), self.payload[start:end+1])
        with self.request({'Range': 'bytes=100-199'}, method='HEAD') as r:
            self.assertEqual(r.status, 206)
            self.assertEqual(r.headers['Content-Length'], '100')
            self.assertEqual(r.read(), b'')

    def test_invalid_and_stale_range(self):
        for value in ['bytes=999999-', 'bytes=200-100', 'bytes=-0']:
            with self.subTest(value=value), self.assertRaises(urllib.error.HTTPError) as error:
                self.request({'Range': value})
            self.assertEqual(error.exception.code, 416)
            self.assertEqual(error.exception.headers['Content-Range'], 'bytes */{}'.format(len(self.payload)))
            error.exception.close()
        with self.request({'Range': 'bytes=100-199', 'If-Range': 'Thu, 01 Jan 1970 00:00:00 GMT'}) as r:
            self.assertEqual(r.status, 200)
            self.assertEqual(r.read(), self.payload)


if __name__ == '__main__':
    unittest.main()
