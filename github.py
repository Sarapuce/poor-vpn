import requests
from base64 import b64encode
from nacl import encoding, public

def encrypt(public_key, secret_value):
  """Encrypt a Unicode string using the public key."""
  public_key = public.PublicKey(public_key.encode("utf-8"), encoding.Base64Encoder())
  sealed_box = public.SealedBox(public_key)
  encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
  return b64encode(encrypted).decode("utf-8")

class github:
  
  def __init__(self, github_token, repo, vpn_workflow_name):
    self.token             = github_token
    self.repo              = repo
    self.vpn_workflow_name = vpn_workflow_name
    self.key_id            = ""
    self.key               = ""
    self.test_config()

  def generate_headers(self):
    return {
      "Accept": "application/vnd.github+json",
      "Authorization": f"Bearer {self.token}",
      "X-GitHub-Api-Version": "2022-11-28"
    }

  def test_config(self):
    headers = self.generate_headers()
    url = f"https://api.github.com/repos/{self.repo}"
    r = requests.get(url, headers=headers)
    r.raise_for_status()

  def get_public_key(self):
    headers = self.generate_headers()
    url = f"https://api.github.com/repos/{self.repo}/actions/secrets/public-key"
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    key_info = r.json()
    
    self.key_id = key_info["key_id"]
    self.key    = key_info["key"]

  def set_tailscale_secret(self, tailscale_token):
    if not self.key_id or not self.key:
      self.get_public_key()

    headers = self.generate_headers()
    data = {
      "encrypted_value": encrypt(self.key, tailscale_token),
      "key_id": self.key_id
    }
    url = f"https://api.github.com/repos/{self.repo}/actions/secrets/TAILSCALE_TOKEN"
    r = requests.put(url, headers=headers, json=data)
    r.raise_for_status()


