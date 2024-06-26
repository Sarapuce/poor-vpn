import os
import time
import json
import typer
import github
import atexit
import shutil
import tailscale
import subprocess

app = typer.Typer()

CONFIG_FILE = "config.json"
PWD         = os.path.dirname(os.path.abspath(__file__))

def read_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            try:
              return json.load(f)
            except:
              return {}
    return {}

def write_config(config_data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config_data, f, indent=4)

def check_config(config):
    parameters_needed = [
        "repo",
        "action_name",
        "tailscale_auth_token",
        "tailscale_auth_token_id",
        "tailscale_api_token",
        "github_token",
        "safe_mode"
    ]
    config_valid = True
    for parameter in parameters_needed:
        config_valid = config_valid and parameter in config
    return config_valid

def print_error(s):
    typer.echo(typer.style(s, fg=typer.colors.RED))

def print_info(s):
    typer.echo(typer.style(s, fg=typer.colors.GREEN))

def validate_yes_no(value: str) -> bool:
    """Validate user input as 'y' or 'n' and convert to boolean."""
    if value.lower() in ['y', 'yes']:
        return True
    elif value.lower() in ['n', 'no']:
        return False
    else:
        raise typer.BadParameter("Please enter 'y' for yes or 'n' for no.")

def unplug_tailscale():
    print_info("[+] Unplugging tailscale exit node")
    command = [f"{PWD}/tailscale_down.sh"]
    _, stderr = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True).communicate()
    if stderr:
        print_error(f"[-] Failed to execute `{' '.join(command)}`")
        print_error(stderr)

def start_vpn(github_client, tailscale_client):
    github_client.trigger_vpn()
    print_info("[+] Waiting for tailscale to setup...")
    if not github_client.wait_tail_scale_setup():
        print_error("[-] Tailscale not setup after 60 seconds")
        exit(1)
    print_info("[+] Tailscale is up")

    time.sleep(1)
    vpn_ip = tailscale_client.get_vpn_ip()
    print_info(f"[+] VPN ip : {vpn_ip}")
    return vpn_ip

def connect_vpn(vpn_ip):
    command = [f"{PWD}/tailscale_up.sh", vpn_ip]
    _, stderr = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True).communicate()
    if stderr:
        print_error(f"[-] Failed to execute `{' '.join(command)}`")
        print_error(stderr)
        exit()
    print_info("[+] Connected!")

def ping(host, ping_count=3, timeout=10):
    command = ["ping", f"{host}", "-c", f"{ping_count}", "-w", f"{timeout}"]
    output = subprocess.Popen(command, stdout=subprocess.PIPE, encoding="utf-8")

    for line in output.stdout:
        if "received" in line:
            packet_received = line.split(",")[1].split(" ")[1]
            return int(packet_received) > 0
    return False

def is_sudo():
    return not os.geteuid()

def is_tailscale():
    return shutil.which("tailscale") is not None

@app.command()
def setup():
    """Setup the various variables needed to work with poor-vpn"""
    config = read_config()

    repo                 = typer.prompt(f"Enter the repo [{config.get('repo', 'sarapuce/poor-vpn')}]", default=config.get("repo", "sarapuce/poor-vpn"), show_default=False)
    action_name          = typer.prompt(f"Enter the action file name [{config.get('action_name', 'vpn.yaml')}]", default=config.get("action_name", "vpn.yaml"), show_default=False)
    github_token         = typer.prompt(f"Enter your github token [{8 * bool(len(config.get('github_token', ''))) * '*'}]", default=config.get("github_token", ""), show_default=False, hide_input=True)
    tailscale_api_token  = typer.prompt(f"Enter your tailscale api token [{8 * bool(len(config.get('tailscale_api_token', ''))) * '*'}]", default=config.get("tailscale_api_token", ""), show_default=False, hide_input=True)
    reset_auth           = typer.prompt("Do you want to reset tailscale auth token? (y/N)", default="n", show_default=False) in ["y", "Y", "yes", "Yes"]
    safe_mode            = typer.prompt("Do you want to enable safe mode? (Y/n)", default="y", show_default=False) not in ["n", "N", "no", "No"]

    config["repo"]                 = repo
    config["action_name"]          = action_name
    config["github_token"]         = github_token
    config["tailscale_api_token"]  = tailscale_api_token
    config["safe_mode"]            = safe_mode

    write_config(config)
    g = github.github(github_token, repo, action_name)
    print_info("[+] Connected to Github!")
    t = tailscale.tailscale(tailscale_api_token)
    print_info("[+] Connected to Tailscale!")

    check_acl = t.check_acl()
    if check_acl:
        print_error(f"[-] {check_acl}")
        exit()

    if reset_auth and config.get("tailscale_auth_token_id", ""):
        t.delete_key(config["tailscale_auth_token_id"])
        config["tailscale_auth_token_id"] = ""

    if not config.get("tailscale_auth_token_id", "") or not t.verify_auth_keys(config["tailscale_auth_token_id"]):
        key = t.create_auth_key()
        config["tailscale_auth_token"] = key["key"]
        config["tailscale_auth_token_id"] = key["id"]
        write_config(config)
        print_info("[+] Generated auth token for tailscale...")
        g.set_tailscale_secret(config["tailscale_auth_token"])

    print_info("[+] Configuration saved!")

@app.command()
def connect():
    if not is_sudo():
        print_error("[-] To use tailscale, this script must be executed as root")
        exit()
    
    if not is_tailscale():
        print_error("[-] To use tailscale, tailscale must be installed and in the path of the root user")
        exit()
    
    config = read_config()
    if not check_config(config):
        print_error("[-] Please start vpn.py setup to configure the application")
        exit(1)
    print_info("[+] Config loaded!")
    
    g = github.github(config["github_token"], config["repo"], config["action_name"])
    print_info("[+] Connected to Github!")

    t = tailscale.tailscale(config["tailscale_api_token"])
    print_info("[+] Connected to Tailscale!")

    if not t.verify_auth_keys(config["tailscale_auth_token_id"]):
        print_error("Tailscale auth key is invalid, please generate it with python3 vpn.py setup")

    vpn_deleted = t.kill_vpns()
    if vpn_deleted == -1:
        print_error("[-] Can't delete some workflow, are they still running ?")
    if vpn_deleted:
        print_info(f"[+] Removed {vpn_deleted} old VPN{'s' * bool(vpn_deleted - 1)}")

    if g.delete_runs():
        print_info("[+] Deleted all old workflow runs")

    atexit.register(g.stop_runs)
    vpn_ip = start_vpn(g, t)
    
    if not config["safe_mode"]:
        atexit.register(unplug_tailscale)
    connect_vpn(vpn_ip)

    top = time.time()
    while(True):
        if not ping(vpn_ip):
            if config["safe_mode"]:
                print_info("[+] Safe mode activated, not disabling tailscale.")
                exit(1)
            unplug_tailscale()
            if not ping("google.com"):
                print_error("[-] Can't connect to google.com without VPN, your internet connexion is probably down")
            else:
                if not ping(vpn_ip): # Catch the case where the connexion get back during the ping to google
                    print_info("[+] VPN seems down, reconnecting...")
                    vpn_ip = start_vpn(g, t)
            connect_vpn(vpn_ip)

        if not config["safe_mode"] and time.time() - top > 6900:
            print_info("[+] Creating a new VPN to avoid timeout")
            vpn_ip = start_vpn(g, t)
            connect_vpn(vpn_ip)
            top = time.time()
        
        time.sleep(5)

@app.command()
def test():
    config = read_config()
    if not check_config(config):
        print_error("[-] Please start vpn.py setup to configure the application")
        exit(1)

    g = github.github(config["github_token"], config["repo"], config["action_name"])
    print_info("[+] Connected to Github!")

    print(g.get_run_ids())
    print(g.get_run_ids(include_completed=False))
    



if __name__ == "__main__":
    app()
