FROM jupyterhub/jupyterhub:4.0

# Install dependencies
RUN pip install --no-cache-dir \
    dockerspawner \
    oauthenticator \
    jupyterhub-nativeauthenticator

# Copy configuration
COPY jupyterhub_config.py /srv/jupyterhub/jupyterhub_config.py

# Create directories
RUN mkdir -p /srv/jupyterhub/notebooks /srv/jupyterhub/data

# Set working directory
WORKDIR /srv/jupyterhub

# Expose port
EXPOSE 8000

# Start JupyterHub
CMD ["jupyterhub", "-f", "/srv/jupyterhub/jupyterhub_config.py"]
