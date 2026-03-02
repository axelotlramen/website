import requests

class WebhookClient:
    def __init__(self, webhook: str):
        self.webhook = webhook

    def send(self, payload: dict):
        response = requests.post(self.webhook, json=payload, timeout=10)
        response.raise_for_status()