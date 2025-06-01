import os
from dockerspawner import DockerSpawner
from nativeauthenticator import NativeAuthenticator

# JupyterHub configuration
c = get_config()

# Basic settings
c.JupyterHub.ip = "0.0.0.0"
c.JupyterHub.port = 8000
c.JupyterHub.hub_ip = "0.0.0.0"
c.JupyterHub.hub_port = 8081

# Use Docker spawner
c.JupyterHub.spawner_class = DockerSpawner

# Docker spawner configuration
c.DockerSpawner.image = os.environ.get(
    "DOCKER_NOTEBOOK_IMAGE", "custom-minimal-notebook:latest"
)
c.DockerSpawner.network_name = os.environ.get(
    "DOCKER_NETWORK_NAME", "astronomy-jupyterhub_default"
)
c.DockerSpawner.remove = True
c.DockerSpawner.debug = True

# Prevent pulling images - use local images only
c.DockerSpawner.pull_policy = "never"

# Mount shared directories and student work directories directly to host filesystem
# Get the host path from environment variable (set by docker-compose)
host_path = os.environ.get("JUPYTERHUB_HOST_PATH", os.getcwd())

c.DockerSpawner.volumes = {
    f"{host_path}/notebooks": {
        "bind": "/home/jovyan/templates",
        "mode": "ro",
    },
    f"{host_path}/data": {
        "bind": "/home/jovyan/data",
        "mode": "ro",
    },
    f"{host_path}/student_work/{{username}}": {
        "bind": "/home/jovyan/",
        "mode": "rw",
    },
}

# Container settings
c.DockerSpawner.extra_create_kwargs = {
    "user": "1000:100"  # jovyan user in jupyter containers
}

# Notebook directory
c.DockerSpawner.notebook_dir = "/home/jovyan"

# Memory and CPU limits
c.DockerSpawner.mem_limit = "8G"
c.DockerSpawner.cpu_limit = 2.0

# Authentication - Using NativeAuthenticator for secure self-registration
c.JupyterHub.authenticator_class = NativeAuthenticator

# Allow users to create their own accounts with custom passwords
c.NativeAuthenticator.enable_signup = True
c.NativeAuthenticator.ask_email_on_signup = False  # Optional email
c.NativeAuthenticator.minimum_password_length = 8
c.NativeAuthenticator.check_common_password = True

# Auto-approve new user signups (for classroom convenience)
# In production, you might want manual approval
c.NativeAuthenticator.open_signup = True

# Explicitly allow all users (important for NativeAuthenticator)
c.NativeAuthenticator.allow_all = True

# Remove any user restrictions - allow any user to sign up
c.Authenticator.allowed_users = set()  # Empty set allows anyone

# Admin users - these will need to be created first with strong passwords
c.Authenticator.admin_users = {"instructor"}

# Enable admin access
c.JupyterHub.admin_access = True

# Database
c.JupyterHub.db_url = "sqlite:///jupyterhub.sqlite"

# Cookie settings
c.JupyterHub.cookie_secret_file = "/srv/jupyterhub/cookie_secret"

# Logo and custom templates
c.JupyterHub.logo_file = "/srv/jupyterhub/logo.png"
c.JupyterHub.template_paths = ["/srv/jupyterhub/templates"]

# Shutdown settings
c.JupyterHub.cleanup_servers = True
c.JupyterHub.cleanup_proxy = True

# Hub startup
c.JupyterHub.hub_connect_ip = "jupyterhub"

# Enable spawner debug mode
c.DockerSpawner.debug = True


# Pre-spawn hook to create student work directories
def pre_spawn_hook(spawner):
    """Create student work directory on host filesystem"""
    import os
    import stat

    username = spawner.user.name
    # Use the mounted path inside the JupyterHub container
    work_dir = f"/srv/jupyterhub/student_work/{username}"

    # Create the student's work directory if it doesn't exist
    os.makedirs(work_dir, mode=0o755, exist_ok=True)

    # Set proper permissions (readable/writable by user)
    try:
        os.chmod(
            work_dir,
            stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH,
        )
        spawner.log.info(f"Created/verified work directory: {work_dir}")
    except Exception as e:
        spawner.log.warning(f"Could not set permissions on {work_dir}: {e}")


c.DockerSpawner.pre_spawn_hook = pre_spawn_hook


# Post-spawn hook to copy template notebooks
def post_spawn_hook(spawner):
    """Copy template notebooks to user's work directory"""
    import subprocess
    import time

    # Copy template notebooks to user's work directory
    username = spawner.user.name
    container_name = f"jupyter-{username}"

    # Wait a moment for container to be fully ready
    time.sleep(2)

    # Commands to run in the container after spawn
    commands = [
        f"docker exec {container_name} bash -c 'cp -r /home/jovyan/templates/* /home/jovyan/work/ 2>/dev/null || true'",
        f"docker exec {container_name} bash -c 'chown -R jovyan:users /home/jovyan/work/ 2>/dev/null || true'",
    ]

    for cmd in commands:
        try:
            subprocess.run(cmd, shell=True, check=False, timeout=30)
            spawner.log.info(f"Executed post-spawn command: {cmd}")
        except Exception as e:
            spawner.log.warning(
                f"Post-spawn command failed (non-critical): {cmd}, error: {e}"
            )


c.DockerSpawner.post_start_hook = post_spawn_hook

# Logging
c.JupyterHub.log_level = "INFO"
c.DockerSpawner.log_level = "INFO"
