"""Serve report artifacts with byte ranges for browser video seeking."""
import argparse
import functools
import os
import re
from email.utils import parsedate_to_datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from .common import PROJECT


class ReportHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Accept-Ranges', 'bytes')
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()

    def send_head(self):
        self.byte_range = None
        path = Path(self.translate_path(self.path))
        try:
            path.resolve().relative_to(Path(self.directory).resolve())
        except ValueError:
            self.send_error(403)
            return None
        header = self.headers.get('Range', '')
        match = re.fullmatch(r'bytes=(\d*)-(\d*)', header)
        if not path.is_file() or not match or not any(match.groups()):
            return super().send_head()
        try:
            source = path.open('rb')
        except OSError:
            self.send_error(404)
            return None
        stat = os.fstat(source.fileno())
        size = stat.st_size
        # An outdated If-Range validator requires a complete representation.
        validator = self.headers.get('If-Range')
        if validator:
            try:
                valid = parsedate_to_datetime(validator).timestamp() >= int(stat.st_mtime)
            except (TypeError, ValueError, OverflowError):
                valid = False
            if not valid:
                source.close()
                return super().send_head()
        first, last = match.groups()
        if first:
            start = int(first)
            end = min(int(last), size - 1) if last else size - 1
        else:
            suffix = int(last)
            start, end = max(0, size - suffix), size - 1
        if start >= size or start > end:
            source.close()
            self.send_response(416)
            self.send_header('Content-Range', 'bytes */{}'.format(size))
            self.send_header('Content-Length', '0')
            self.end_headers()
            return None
        self.send_response(206)
        self.send_header('Content-Type', self.guess_type(str(path)))
        self.send_header('Content-Range', 'bytes {}-{}/{}'.format(start, end, size))
        self.send_header('Content-Length', str(end - start + 1))
        self.send_header('Last-Modified', self.date_time_string(stat.st_mtime))
        self.end_headers()
        source.seek(start)
        self.byte_range = (start, end)
        return source

    def copyfile(self, source, outputfile):
        try:
            if self.byte_range is None:
                return super().copyfile(source, outputfile)
            remaining = self.byte_range[1] - self.byte_range[0] + 1
            while remaining:
                chunk = source.read(min(1024 * 1024, remaining))
                if not chunk:
                    break
                outputfile.write(chunk)
                remaining -= len(chunk)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            # Seeking cancels the previous video request in normal browsers.
            pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bind', default='0.0.0.0')
    parser.add_argument('--port', default=8765, type=int)
    parser.add_argument('--directory', default=str(PROJECT / 'outputs'))
    args = parser.parse_args()
    handler = functools.partial(ReportHandler, directory=str(Path(args.directory).resolve()))
    with ThreadingHTTPServer((args.bind, args.port), handler) as server:
        print('Report server http://{}:{}/ (video byte ranges enabled)'.format(args.bind, args.port), flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()
