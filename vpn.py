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

@app.command()
def setup():
    """Setup the various variables needed to work with poor-vpn"""
    config = read_config()

    repo            = typer.prompt(f"Enter the repo [{config.get('repo', 'sarapuce/poor-vpn')}]", default=config.get("repo", "sarapuce/poor-vpn"), show_default=False)
    action_name     = typer.prompt(f"Enter the action file name [{config.get('action_name', 'vpn.yaml')}]", default=config.get("action_name", "vpn.yaml"), show_default=False)
    github_token    = typer.prompt(f"Enter your github token [{8 * bool(len(config.get('github_token', ''))) * '*'}]", default=config.get("github_token", ""), show_default=False, hide_input=True)
    tailscale_token = typer.prompt(f"Enter your tailscale token [{8 * bool(len(config.get('tailscale_token', ''))) * '*'}]", default=config.get("tailscale_token", ""), show_default=False, hide_input=True)

    config["repo"]            = repo
    config["action_name"]     = action_name
    config["github_token"]    = github_token
    config["tailscale_token"] = tailscale_token

    write_config(config)
    g = github.github(github_token, repo, action_name)
    typer.echo("Connected to Github!")
    g.set_tailscale_secret(tailscale_token)
    typer.echo("Configuration saved!")

@app.command()
def connect():
    pass


if __name__ == "__main__":
    app()
