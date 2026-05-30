"""Web utilities — health check server для Railway."""

import os
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

logger = logging.getLogger(__name__)

HEALTH_PORT = int(os.environ.get("PORT", 8000))


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status":"ok","service":"img-edit-bot"}')

    def log_message(self, format, *args):
        logger.debug(f"Health: {format % args}")


def start_health_server():
    server = HTTPServer(("0.0.0.0", HEALTH_PORT), HealthHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    logger.info(f"❤️ Health server on port {HEALTH_PORT}")
