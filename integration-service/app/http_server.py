import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .common import configure_logging, log


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None: 
        if self.path != "/health":
            self.send_error(404)
            return
        body = json.dumps({"status": "ok", "service": "integration-service"}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_: object) -> None:
        return


def main() -> None:
    port = int(os.getenv("HEALTH_PORT", "8080"))
    logger = configure_logging()
    log(logger, "INFO", "health_server_started", port=port)
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
