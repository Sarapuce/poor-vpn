import json
import os
import typer
import github

app = typer.Typer()

CONFIG_FILE = "config.json"

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
    return "repo" in config and "action_name" in config and "github_action" in config and "tailscale_auth_token" in config and "tailscale_api_token" in config

def print_error(s):
    typer.echo(typer.style(s, fg=typer.colors.RED))

def print_info(s):
    typer.echo(typer.style(s, fg=typer.colors.GREEN))

@app.command()
def setup():
    """Setup the various variables needed to work with poor-vpn"""
    config = read_config()

    repo                 = typer.prompt(f"Enter the repo [{config.get('repo', 'sarapuce/poor-vpn')}]", default=config.get("repo", "sarapuce/poor-vpn"), show_default=False)
    action_name          = typer.prompt(f"Enter the action file name [{config.get('action_name', 'vpn.yaml')}]", default=config.get("action_name", "vpn.yaml"), show_default=False)
    github_token         = typer.prompt(f"Enter your github token [{8 * bool(len(config.get('github_token', ''))) * '*'}]", default=config.get("github_token", ""), show_default=False, hide_input=True)
    tailscale_auth_token = typer.prompt(f"Enter your tailscale auth token [{8 * bool(len(config.get('tailscale_auth_token', ''))) * '*'}]", default=config.get("tailscale_auth_token", ""), show_default=False, hide_input=True)
    tailscale_api_token  = typer.prompt(f"Enter your tailscale api token [{8 * bool(len(config.get('tailscale_api_token', ''))) * '*'}]", default=config.get("tailscale_api_token", ""), show_default=False, hide_input=True)

    config["repo"]                 = repo
    config["action_name"]          = action_name
    config["github_token"]         = github_token
    config["tailscale_auth_token"] = tailscale_auth_token
    config["tailscale_api_token"]  = tailscale_api_token

    write_config(config)
    g = github.github(github_token, repo, action_name)
    print_info("[+] Connected to Github!")
    g.set_tailscale_secret(tailscale_auth_token)
    print_info("[+] Configuration saved!")

@app.command()
def connect():
    config = read_config()
    if not check_config(config):
        print_error("[-] Please start vpn.py setup to configure the application")
        exit(1)
    print_info("[+] Config loaded!")
    
    g = github.github(config["github_token"], config["repo"], config["action_name"])
    print_info("[+] Connected to Github!")


if __name__ == "__main__":
    app()
