import hashlib
from pathlib import Path
from urllib.parse import urlparse

from connectors.http_client import HTTPClient


class FileDownloader:
    def __init__(self, download_dir='downloads'):
        self.client = HTTPClient(request_interval=1.5)
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)

    def _guess_filename(self, url, default_name='announcement.pdf'):
        parsed = urlparse(url)
        name = Path(parsed.path).name
        return name or default_name

    def download(self, url, filename=None):
        response = self.client.get(url)
        filename = filename or self._guess_filename(url)
        file_path = self.download_dir / filename
        file_path.write_bytes(response.content)

        file_hash = hashlib.sha256(response.content).hexdigest()

        return {
            'file_path': str(file_path),
            'file_hash': file_hash,
            'content_type': response.headers.get('Content-Type', ''),
            'size_bytes': len(response.content)
        }
