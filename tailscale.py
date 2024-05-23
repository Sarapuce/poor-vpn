import requests

class tailscale:

  def __init__(self, tailscale_token):
    self.token = tailscale_token
    self.test_config()

  def test_config(self):
    headers = {"Authorization": f"Bearer {self.token}"}
    url = "https://api.tailscale.com/api/v2/tailnet/-/devices"
    r = requests.get(url, headers=headers)
    r.raise_for_status()
