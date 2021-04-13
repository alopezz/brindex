import asyncio
from http.server import BaseHTTPRequestHandler, HTTPServer

from brindex._asyncutils import run_async, wrap_sync_reader, wrap_sync_writer
from brindex._html import make_html_list_page
from brindex.repo import LocalRepo, S3Repo


async def _async_copy_stream(input_stream, output_stream):
    chunk_size = 64 * 1024
    q = asyncio.Queue(maxsize=1)

    async def read_loop():
        while True:
            chunk = await input_stream.read(chunk_size)
            await q.put(chunk)
            if not chunk:
                break

    async def write_loop():
        while True:
            chunk = await q.get()
            if not chunk:
                q.task_done()
                break
            await output_stream.write(chunk)
            q.task_done()

    read_task = asyncio.ensure_future(read_loop())
    write_task = asyncio.ensure_future(write_loop())

    try:
        await asyncio.gather(read_task, write_task)
    finally:
        read_task.cancel()
        write_task.cancel()


def copy_stream(input_stream, output_stream):
    # Wrap async copy into a sync function
    return run_async(_async_copy_stream(input_stream, output_stream))


def _make_handler(callback):
    class BrindexHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            try:
                response = callback(self.path)
            # For now we use KeyError as an indication of a package
            # not being present
            except KeyError:
                self.send_error(400)
                return
            except RuntimeError:
                self.send_error(500)
                return

            self.send_response(200)
            self.send_header("content-type", response.content_type)
            self.end_headers()
            response.write(self.wfile)

    return BrindexHandler


class _HTMLResponse:
    content_type = "text/html"

    def __init__(self, content):
        self.content = content

    def write(self, wfile):
        wfile.write(self.content.encode("utf8"))


class _WhlResponse:
    content_type = "application/zip"

    def __init__(self, stream_factory):
        self.stream_factory = stream_factory

    async def _async_write(self, wfile):
        async with self.stream_factory() as stream:
            await _async_copy_stream(
                stream,
                wrap_sync_writer(wfile)
            )

    def write(self, wfile):
        if hasattr(self.stream_factory(), "__aenter__"):
            run_async(self._async_write(wfile))
        else:
            with self.stream_factory() as stream:
                copy_stream(
                    wrap_sync_reader(stream),
                    wrap_sync_writer(wfile)
                )


class BrindexServer:
    def __init__(self, repo):
        self.repo = repo

    def handle_request(self, path):
        path_elems = path.strip("/").split("/")

        if len(path_elems) == 1:
            if not path_elems[0]:
                elements = [f"{k}/" for k in self.repo.keys()]
                prefix = ""
            else:
                elements = self.repo[path_elems[0]]
                prefix = f"/{path_elems[0]}"

            return _HTMLResponse(make_html_list_page(elements, prefix))

        elif len(path_elems) == 2:
            package, artifact = path_elems
            return _WhlResponse(self.repo[package][artifact].download())

        else:
            raise RuntimeError("Bad path")

    def _make_server(self, port):
        handler = _make_handler(self.handle_request)
        self.server = HTTPServer(("", port), handler)

    def start_server(self, port=8000):
        self._make_server(port)
        self.server.serve_forever()

    def shutdown(self):
        self.server.shutdown()


def main():
    import argparse
    import signal
    import sys

    parser = argparse.ArgumentParser()
    parser.add_argument("--s3",
                        help="S3 bucket name")
    parser.add_argument("--local",
                        help="Path to local repo root")
    parser.add_argument("--port", default=8000, type=int)

    args = parser.parse_args()

    if args.s3 and args.local:
        print("Only one of '--s3' or '--local' can be specified")
        sys.exit(1)

    if not args.s3 and not args.local:
        print("Either '--s3' or '--local' must be specified")
        sys.exit(1)

    if args.s3:
        repo = S3Repo(args.s3)

    elif args.local:
        repo = LocalRepo(args.local)

    server = BrindexServer(repo)

    # Setup a signal to avoid SIGINT showing an ugly traceback
    def _sigint_handler(signum, stack_frame):
        print("Shutdown signal received")
        sys.exit(0)

    signal.signal(signal.SIGINT, _sigint_handler)

    server.start_server(port=args.port)


if __name__ == '__main__':
    main()
