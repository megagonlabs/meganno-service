# meganno-service

These are RESTful API services for the meganno platform.

![version](https://img.shields.io/badge/api--latest-v1.2.0-blue)
![version](https://img.shields.io/badge/auth--latest-v1.0.0-blue)

## Set up services

### Generate an encryption key

```python
from cryptography.fernet import Fernet
Fernet.generate_key().decode()
```

### Create .env

```env
MEGANNO_PROJECT_NAME=meganno
MEGANNO_PROJECT_DIR=./meganno_data
MEGANNO_SERVICE_PORT=5000
MEGANNO_AUTH_PORT=5001
MEGANNO_NEO4J_PASSWORD=meganno
MEGANNO_ADMIN_USERNAME=admin
MEGANNO_ADMIN_PASSWORD=
MEGANNO_ENCRYPTION_KEY=
MEGANNO_IMAGE=api-1.2.0
MEGANNO_AUTH_IMAGE=auth-1.0.0
```

| Variable                | Default          | Description                                                                         |
| :---------------------- | :--------------- | :---------------------------------------------------------------------------------- |
| MEGANNO_PROJECT_NAME    | meganno          | Name of the meganno project                                                         |
| MEGANNO_PROJECT_DIR     | ./meganno_data   | Root directory for Neo4j database folders such as `data/`, `logs/`, and `instance/` |
| MEGANNO_SERVICE_PORT    | 5000             | API service port                                                                    |
| MEGANNO_AUTH_PORT       | 5001             | Authentication service port                                                         |
| MEGANNO_AUTH_HOST       |                  | For multi-project set up (ignore otherwise)                                         |
| MEGANNO_NEO4J_PASSWORD  | meganno          | Password for Neo4j database                                                         |
| MEGANNO_ADMIN_USERNAME  | admin            | Adminitrator username for default admin. account (only needed it for auth service)  |
| MEGANNO_ADMIN_PASSWORD  |                  | Adminitrator password for default admin. account (only needed it for auth service)  |
| MEGANNO_ENCRYPTION_KEY  |                  | Fernet encryption key (only needed it for auth service)                             |
| MEGANNO_IMAGE           | api-1.2.0        | Docker image tag                                                                    |
| MEGANNO_AUTH_IMAGE      | auth-1.0.0       | Docker image tag for auth service                                                   |

### Install Docker

```bash
sudo yum update -y
sudo yum install docker -y
sudo service docker start
```

### Install Docker Compose plugin

```bash
sudo -i
mkdir -p ~/.docker/cli-plugins/
curl -SL https://github.com/docker/compose/releases/download/v2.2.3/docker-compose-linux-x86_64 -o ~/.docker/cli-plugins/docker-compose
chmod +x ~/.docker/cli-plugins/docker-compose
exit
```

### Start meganno-service backend

> Both `single-project.yaml` and `.env` files should be under the same directory.

```bash
sudo docker compose -f single-project.yaml up -d
```

### Multi-project auth set up
You can configure multiple projects to connect to the same backend auth server. With this set up, users do not have to recreate their accounts for individual projects under the same team.
```bash
# replace {MEGANNO_AUTH_PORT}, {MEGANNO_PROJECT_DIR}
# with default values or values in .env file
sudo docker run --env-file .env -p {MEGANNO_AUTH_PORT}:{MEGANNO_AUTH_PORT} -p 43259:43259 -v "$(pwd)/{MEGANNO_PROJECT_DIR}/instance:/instance" -v "$(pwd)/{MEGANNO_PROJECT_DIR}/logs/auth:/logs" -td megagonlabs/meganno-service:auth-1.0.0

sudo docker compose -f multi-project.yaml up -d
```

## Testing
```bash
cd tests/
pip install -r requirements.txt
pytest -sv integration_test/
pytest -sv core_test/
```