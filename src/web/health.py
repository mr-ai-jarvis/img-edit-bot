"""Web utilities — health check + временный хостинг изображений для Pollinations."""

import os
import re
import uuid
import logging
import threading
import pathlib
from http.server import HTTPServer, BaseHTTPRequestHandler

logger = logging.getLogger(__name__)

HEALTH_PORT = int(os.environ.get("PORT", 8000))

# Временное хранилище для изображений
TEMP_DIR = pathlib.Path("/tmp/img-edit-bot")
TEMP_DIR.mkdir(parents=True, exist_ok=True)


def save_temp_image(image_bytes: bytes, ext: str = "jpg") -> str:
    """Сохранить изображение во временную папку и вернуть UUID."""
    file_id = str(uuid.uuid4())
    file_path = TEMP_DIR / f"{file_id}.{ext}"
    with open(file_path, "wb") as f:
        f.write(image_bytes)
    logger.info(f"Saved temp image: {file_path}")
    return file_id


def get_temp_url(file_id: str, ext: str = "jpg") -> str:
    """Получить публичный URL для временного изображения."""
    # Пытаемся определить Railway URL
    railway_url = os.environ.get("RAILWAY_PUBLIC_DOMAIN")
    if railway_url:
        return f"https://{railway_url}/temp/{file_id}.{ext}"
    return f"/temp/{file_id}.{ext}"


def cleanup_temp_files(max_age_seconds: int = 300):
    """Удалить старые временные файлы (по умолчанию старше 5 минут)."""
    import time
    now = time.time()
    deleted = 0
    for f in TEMP_DIR.iterdir():
        if f.is_file() and now - f.stat().st_mtime > max_age_seconds:
            f.unlink(missing_ok=True)
            deleted += 1
    if deleted:
        logger.info(f"Cleaned up {deleted} old temp files")


class ImgEditHandler(BaseHTTPRequestHandler):
    """HTTP-сервер: health check + временный хостинг изображений."""

    def do_GET(self):
        # Health check
        if self.path == "/" or self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"ok","service":"img-edit-bot"}')
            return

        # Serve temp image
        match = re.match(r"^/temp/([a-f0-9\-]+)\.(jpg|jpeg|png)$", self.path)
        if match:
            file_id = match.group(1)
            ext = match.group(2)
            file_path = TEMP_DIR / f"{file_id}.{ext}"

            if file_path.exists():
                self.send_response(200)
                if ext in ("jpg", "jpeg"):
                    self.send_header("Content-Type", "image/jpeg")
                else:
                    self.send_header("Content-Type", "image/png")
                self.send_header("Cache-Control", "no-cache, max-age=300")
                self.end_headers()
                with open(file_path, "rb") as f:
                    self.wfile.write(f.read())
                logger.debug(f"Served temp image: {file_path}")
                return
            else:
                self.send_response(404)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"error":"image not found"}')
                return

        self.send_response(404)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"error":"not found"}')

    def log_message(self, format, *args):
        logger.debug(f"HTTP: {format % args}")


def start_health_server():
    server = HTTPServer(("0.0.0.0", HEALTH_PORT), ImgEditHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    logger.info(f"❤️ Health server on port {HEALTH_PORT}")

    # Cleanup old files every 5 minutes
    import threading as _threading
    def cleanup_loop():
        import time
        while True:
            time.sleep(300)
            cleanup_temp_files()
    cthread = _threading.Thread(target=cleanup_loop, daemon=True)
    cthread.start()
