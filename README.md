# poor-vpn

Bug :
- Can get a 403 at start if the github action of the old vpn is still running, just try again in 10 seconds -> If a 403 is detected, stop all runs, wait 10 secondes and retry (TODO)
- If there is an instability the github action and the VPN goes down, a new one will be reopen. During the reinitialisation time, all your actions will be done with your real IP -> Implementing safe mode which won't execute tailscale down

Test :
- Connected to VPN, kill the Github action. Does a new one will be triggered ?
- Connected to the VPN, kill the internet connexion, will tailscale will reuse the same runner ?
