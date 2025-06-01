# JupyterHub for Astronomy Education 🔭

A Docker-based JupyterHub instance designed for astronomy education where students can access astronomical datasets and work with the prose library for professional astronomical data analysis.

## Features ✨

- **🔭 Astronomy-Focused Environment**: Pre-installed prose library for astronomical data processing
- **👥 Multi-user Environment**: Students get isolated notebook environments with individual accounts
- **📊 Professional Data Analysis**: Astropy, Photutils, and other astronomy libraries included
- **📓 Sample Notebooks**: Pre-built analysis templates demonstrating prose functionality
- **🐳 Docker-based**: Easy deployment and consistent environments
- **🔐 Secure Authentication**: Individual user accounts with personal passwords
- **🗂️ Version Control Ready**: Complete git integration with comprehensive .gitignore

## Quick Start 🚀

### Prerequisites

- Docker and Docker Compose installed
- At least 4GB RAM available (8GB+ recommended for FITS processing)
- Port 8000 available

### 1. Clone and Setup

```bash
git clone <your-repo> astronomy-jupyterhub
cd astronomy-jupyterhub
```

### 2. Start the Environment

```bash
docker-compose up -d
```

### 3. Access JupyterHub

Open your browser and navigate to: `http://localhost:8000`

**For Students:**
- Click "Sign up" to create your own account
- Choose a unique username and secure password (8+ characters)
- Your personal workspace will be created automatically

**For Instructors:**
- Create admin accounts for 'instructor' usernames
- Access admin panel at: http://localhost:8000/hub/admin

**For Students:**
- Click "Sign up" to create a new account
- Choose your own username and secure password
- Start using JupyterHub immediately after signup

### 4. Stop the Environment

```bash
docker-compose down
```

## Architecture 🏗️

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   JupyterHub    │────│ Docker Spawner  │────│ Student Notebook│
│   (Port 8000)   │    │                 │    │   Containers    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │ Shared Volumes  │
                    │ - templates/    │
                    │ - data/         │
                    └─────────────────┘
```

## Directory Structure 📁

```
classroom-jupyterhub/
├── docker-compose.yml      # Main Docker Compose configuration
├── Dockerfile             # JupyterHub container definition
├── jupyterhub_config.py   # JupyterHub configuration
├── notebooks/             # Template notebooks (mounted read-only)
│   ├── 00_getting_started.ipynb
│   └── 01_data_analysis_template.ipynb
├── data/                  # Shared datasets (mounted read-only)
│   ├── student_performance.csv
│   └── weather_data.csv
└── README.md
```



## Student Workflow 👩‍🎓👨‍🎓

1. **Login** to JupyterHub with provided credentials
2. **Explore** the getting started notebook to familiarize with the environment
3. **Copy** template notebooks to your work directory
4. **Analyze** the shared datasets
5. **Create** your own notebooks for assignments
6. **Save** your work (automatically persisted between sessions)

## For Instructors 👩‍🏫👨‍🏫

### Adding New Datasets

1. Add CSV files to the `data/` directory
2. Update template notebooks to reference new datasets
3. Restart the JupyterHub service: `docker-compose restart`

### Creating New Templates

1. Create new `.ipynb` files in the `notebooks/` directory
2. Include clear instructions and example code
3. Test with a student account

### Monitoring Usage

- **Admin Panel**: Login as `instructor` or `teacher` and access the admin panel
- **Container Logs**: `docker-compose logs jupyterhub`
- **Resource Usage**: `docker stats`

## Configuration Options ⚙️

### Security Settings

**⚠️ Important**: The default configuration uses `DummyAuthenticator` which is suitable for controlled classroom environments but NOT for production use.

For production environments, consider:
- OAuth authentication (GitHub, Google, etc.)
- LDAP/Active Directory integration
- Custom user databases

### Resource Limits

In `jupyterhub_config.py`:

```python
c.DockerSpawner.mem_limit = '8G'      # Memory per student
c.DockerSpawner.cpu_limit = 2.0       # CPU cores per student
```

### Custom Docker Images

Modify the environment variable in `docker-compose.yml`:

```yaml
environment:
  - DOCKER_NOTEBOOK_IMAGE=jupyter/scipy-notebook:latest
```

Available images:
- `jupyter/minimal-notebook` - Basic Python
- `jupyter/datascience-notebook` - Python, R, Julia
- `jupyter/scipy-notebook` - Scientific Python stack
- `jupyter/tensorflow-notebook` - Machine learning focused

## Troubleshooting 🔧

### Common Issues

**Students can't access data:**
- Check volume mounts in `docker-compose.yml`
- Verify data files exist in `./data/` directory
- Ensure containers have read permissions

**JupyterHub won't start:**
- Check if port 8000 is already in use: `lsof -i :8000`
- Verify Docker daemon is running
- Check logs: `docker-compose logs jupyterhub`

**Out of resources:**
- Reduce memory limits in configuration
- Monitor with `docker stats`
- Consider limiting concurrent users

**Authentication issues:**
- Verify usernames in `allowed_users` list
- Check password in configuration
- Clear browser cookies and try again

### Useful Commands

```bash
# View all containers
docker ps -a

# Access JupyterHub logs
docker-compose logs -f jupyterhub

# Restart specific service
docker-compose restart jupyterhub

# Clean up stopped containers
docker-compose down && docker system prune

# Access a student container
docker exec -it jupyter-student1 bash
```

## Development 🛠️

### Local Development

1. Make changes to configuration files
2. Rebuild and restart:
   ```bash
   docker-compose down
   docker-compose up --build
   ```

### Adding New Libraries

Modify the `Dockerfile.notebook` to install additional Python packages:

```dockerfile
RUN pip install --no-cache-dir \
    your-new-package \
    another-package
```

## Security Considerations 🔒

### For Classroom Use
- Change default password in `jupyterhub_config.py`
- Limit access to classroom network
- Regular backup of student work
- Monitor resource usage

## Support 💬

### Getting Help
- Check the troubleshooting section above
- Review JupyterHub documentation: https://jupyterhub.readthedocs.io/
- Check Docker logs for error messages

### Customization
- Modify `jupyterhub_config.py` for JupyterHub settings
- Edit `docker-compose.yml` for container configuration
- Update notebooks in `notebooks/` directory for new templates

## License 📝

This project is designed for educational use. Please ensure compliance with your institution's IT policies and data handling requirements.

---

**Happy Teaching and Learning! 🎓📊**
