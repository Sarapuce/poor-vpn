import re
import json
import requests
from datetime import datetime, timezone

class tailscale:

  def call_api(self, endpoint, verb='GET', payload={}, json=True):
    # Remove extra / at the start of the endpoint
    if endpoint.startswith('/'):
      endpoint = endpoint[1:]

    headers = {"Authorization": f"Bearer {self.token}"}
    url = f"https://api.tailscale.com/api/v2/{endpoint}"
    if verb == 'GET':
      r = requests.get(url, headers=headers)
    if verb == 'DELETE':
      r = requests.delete(url, headers=headers)
    if verb == 'POST':
      r = requests.post(url, headers=headers, json=payload)
    r.raise_for_status()
    if json:
      return r.json()
    else:
      return r.text
  
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
        try:
          r = self.call_api(f"device/{device['id']}", "DELETE")
        except:
          return -1
        deletion += 1
    return deletion
  
  def get_vpn_ip(self):
    devices = self.call_api("/tailnet/-/devices")["devices"]
    most_recent_device = devices[0]
    for device in devices[1:]:
      if device["created"] > most_recent_device["created"]:
        most_recent_device = device
    print(most_recent_device["addresses"][0])

  def verify_auth_keys(self, key_id):
    keys = self.call_api("/tailnet/-/keys")
    for key in keys["keys"]:
      info = self.call_api(f"/tailnet/-/keys/{key['id']}")
      if info["id"] == key_id:
        # print(info)
        if info["expires"] < str(datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')):
          self.delete_key(key_id)
          return False
        return True
    return False
  
  def delete_key(self, key_id):
    self.call_api(f"tailnet/-/keys/{key_id}", verb='DELETE')
    return True

  def create_auth_key(self):
    payload = {
      "capabilities": {
        "devices": {
          "create": {
            "reusable": True,
            "ephemeral": False,
            "preauthorized": True,
            "tags": ["tag:vpn"]
          }
        }
      }
    }
    key = self.call_api("/tailnet/-/keys", verb="POST", payload=payload)
    return key

  def check_acl(self):
    acl = self.call_api("tailnet/-/acl", json=False)
    acl = re.sub(r'//.*?\n', '', acl)
    acl = re.sub(r'//.*?$', '', acl, flags=re.MULTILINE)
    acl = acl.replace("\n", "").replace("\t", "").replace(",}", "}").replace(",]", "]")
    acl = json.loads(acl)
    if not acl.get("tagOwners", False) or not acl["tagOwners"].get("tag:vpn", False) or not "tag:vpn" in acl["tagOwners"]["tag:vpn"]:
      return "tagOwners field must be configured like this : \"tagOwners\": {\"tag:vpn\": [\"tag:vpn\", \"your@email.com\"]}"
    if not acl.get("autoApprovers", False) or not acl["autoApprovers"].get("exitNode", False) or not "tag:vpn" in acl["autoApprovers"]["exitNode"]:
      return "autoApprovers field must be configured like this : \"autoApprovers\": {\"exitNode\": [\"tag:vpn\", \"your@email.com\"]}"
    return ""
