import requests

class tailscale:

  def call_api(self, endpoint, verb='GET'):
    # Remove extra / at the start of the endpoint
    if endpoint.startswith('/'):
      endpoint = endpoint[1:]

    headers = {"Authorization": f"Bearer {self.token}"}
    url = f"https://api.tailscale.com/api/v2/{endpoint}"
    if verb == 'GET':
      r = requests.get(url, headers=headers)
    if verb == 'DELETE':
      r = requests.delete(url, headers=headers)
    r.raise_for_status()
    return r.json()
  
  def __init__(self, tailscale_token):
    self.token = tailscale_token
    self.test_config()

  def test_config(self):
    self.call_api("tailnet/-/devices")

  def kill_vpns(self):
    deletion = 0
    devices = self.call_api("tailnet/-/devices")
    for device in devices["devices"]:
      if 'tag:vpn' in device.get("tags", ""):
        r = self.call_api(f"device/{device['id']}", "DELETE")
        deletion += 1
    return deletion
