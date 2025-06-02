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
        "bind": "/home/jovyan/example_notebooks",
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
c.DockerSpawner.cpu_limit = 3.0

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
# c.JupyterHub.logo_file = "/srv/jupyterhub/logo.png"  # Logo file not available
# c.JupyterHub.template_paths = ["/srv/jupyterhub/templates"]

# Shutdown settings
c.JupyterHub.cleanup_servers = True
c.JupyterHub.cleanup_proxy = True

# Hub startup
c.JupyterHub.hub_connect_ip = "jupyterhub"

# Enable spawner debug mode
c.DockerSpawner.debug = True

# In your jupyterhub_config.py, add these lines:
c.DockerSpawner.environment = {
    "JUPYTER_RUNTIME_DIR": "/tmp/jupyter-runtime",
    "JUPYTER_DATA_DIR": "/tmp/jupyter-data",
}


# Alternative version with more robust Windows permissions handling
def pre_spawn_hook(spawner):
    """Create student work directory with advanced Windows permissions support"""
    import os
    import stat
    import platform

    username = spawner.user.name

    # Platform-specific path handling
    if platform.system() == "Windows":
        work_dir = os.path.join("C:", "srv", "jupyterhub", "student_work", username)
    else:
        work_dir = f"/srv/jupyterhub/student_work/{username}"

    # Create the student's work directory if it doesn't exist
    try:
        os.makedirs(work_dir, exist_ok=True)
        spawner.log.info(f"Created/verified work directory: {work_dir}")
    except Exception as e:
        spawner.log.error(f"Failed to create work directory {work_dir}: {e}")
        return

    # Set permissions based on platform
    try:
        if platform.system() == "Windows":
            # For Windows, we can try to use the subprocess module to set permissions
            # using icacls (if more granular control is needed)
            import subprocess

            try:
                # Grant full control to the current user
                # This is optional and may require admin privileges
                subprocess.run(
                    ["icacls", work_dir, "/grant", f"{os.getlogin()}:(F)"],
                    check=False,
                    capture_output=True,
                )
                spawner.log.info(f"Set Windows permissions for: {work_dir}")
            except Exception as icacls_error:
                spawner.log.debug(
                    f"Could not set Windows ACL permissions: {icacls_error}"
                )
        else:
            # Unix-style permissions
            os.chmod(
                work_dir,
                stat.S_IRWXU
                | stat.S_IRGRP
                | stat.S_IXGRP
                | stat.S_IROTH
                | stat.S_IXOTH,
            )
            spawner.log.info(f"Set Unix permissions for: {work_dir}")
    except Exception as e:
        spawner.log.warning(f"Could not set permissions on {work_dir}: {e}")
        # Directory still exists and should be usable even without explicit permissions


c.DockerSpawner.pre_spawn_hook = pre_spawn_hook
