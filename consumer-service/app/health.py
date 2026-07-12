import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread


def start_health_server(port: int, state: dict[str, bool]) -> None:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None: 
            if self.path != "/health":
                self.send_error(404)
                return
            ready = state.get("ready", False)
            body = json.dumps({"status": "ok" if ready else "starting", "service": "consumer-service"}).encode()
            self.send_response(200 if ready else 503)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *_: object) -> None:
            return

    Thread(target=ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever, daemon=True).start()
