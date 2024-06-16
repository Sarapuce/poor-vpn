# poor-vpn

This is free way to get a simple VPN. The location of the IP will be in USA.

## Principle

It uses Github runners as an exit node and tailscale to make the connection between your computer and the runner. Tailscale could probably be replaced by something else. (Github if you read this, It is just a PoC I would never use it)

## Requierments
- [Tailscale](https://tailscale.com/) CLI installed
- A [tailscale](https://tailscale.com/) account
- A [Github](https://github.com) account
- [Python](https://www.python.org/downloads/)

## How to use

1. **FORK** the repo, you need to use your own github account with your own Github actions.
2. Create a github token for your repo. It should at least have :
  - Read access to the repo
  - Read access to the github actions
  - Write access to the github actions
  - Write access to secrets
3. In your tailscale account, go to "[Access Controls](https://login.tailscale.com/admin/acls/file)" 
4. Add the following tag `"tag:vpn": ["tag:vpn", "your@mail.com"]` in `tagOwners`
5. Add this list `"exitNode": ["tag:vpn", "your@mail.com"]` to the `autoApprovers` field

| 💡 If you don't have anything else in your tailscale account, you should have this in your ACL :

```
	"tagOwners": {
		"tag:vpn": ["tag:vpn", "your@mail.com"],
		},
	"autoApprovers": {
		"exitNode": ["tag:vpn", "your@mail.com"],
	},
```
6. In tailscale, create an [API access token](https://login.tailscale.com/admin/settings/keys) and copy it

| ⚠️ The key can only be valable 90 days so you will need to rotate it.

7. Clone the repo to your folder `git clone <your-repo>`
8. Install the requirements : `pip3 install -r requirements.txt`
9. Configure the VPN : `python3 vpn.py setup`, for me, I would have entered this :
  - Name of your repo : `sarapuce/poor-vpn`
  - Action file name : `vpn.yaml` (you should probably not change it)
  - Github token : `ghp_Tm9wIGl0J3Mgbm90IHJlYWw` (:
  - Tailscale API token : `tskey-api-bm90YXRhbGw-aXQgZG9lcyBub3Qgd29yaw` (:
  - Reset a tailscale auth token : `y`
  - [Safe mode](#safe-mode) : `y`
10. `sudo python3 vpn.py connect`
11. Enjoy !

## Safe mode
A Github runner last 2 hours. A transfer must be done in case of runner instability or if you want to use the VPN longer. During the transfer, stopping all the traffic seems a bit hard to do. To prevent your real IP to be leaked, the safe mode will simply turn off the VPN and cut your internet connexion.
- Safe mode on : After the end of the VPN, you must manually execute `sudo tailscale set --exit-node=` to regain your internet connexion
- Safe mode off : You don't need to worry, if an instabillity is detected with the github runner, a new one will be restarted but you will use your real IP during the transfer 


## Known bugs :
- Can get a 403 at start if the github action of the old vpn is still running, just try again in 10 seconds -> If a 403 is detected, stop all runs, wait 10 secondes and retry (TODO)
- If there is an instability the github action and the VPN goes down, a new one will be reopen. During the reinitialisation time, all your actions will be done with your real IP -> Implementing safe mode which won't execute tailscale down

