import time
import requests


class HTTPClient:
    def __init__(self, user_agent=None, request_interval=1.5):
        self.session = requests.Session()
        self.request_interval = request_interval
        self.session.headers.update({
            'User-Agent': user_agent or 'RealEstateNewsIntelligence/0.1 (+compliance-first; contact: local-user)'
        })

    def get(self, url, params=None, headers=None, timeout=30):
        time.sleep(self.request_interval)
        response = self.session.get(url, params=params, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response

    def post(self, url, data=None, json=None, headers=None, timeout=30):
        time.sleep(self.request_interval)
        response = self.session.post(url, data=data, json=json, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response
