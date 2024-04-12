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

### Docker
#### Install Docker (on Linux)

> for other system platforms, follow instructions on "[Install Docker Engine](https://docs.docker.com/engine/install/)" to install docker and docker compose.

```bash
sudo yum update -y
sudo yum install docker -y
sudo service docker start
```

#### Install Docker Compose plugin (on Linux)

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

## Disclosure
This software may include, incorporate, or access open source software (OSS) components, datasets and other third party components, including those identified below. The license terms respectively governing the datasets and third-party components continue to govern those portions, and you agree to those license terms may limit any distribution. You may  use any OSS components under the terms of their respective licenses, which may include BSD 3, Apache 2.0, or other licenses. In the event of conflicts between Megagon Labs, Inc. (“Megagon”) license conditions and the OSS license conditions, the applicable OSS conditions governing the corresponding OSS components shall prevail. 
You agree not to, and are not permitted to, distribute actual datasets used with the OSS components listed below. You agree and are limited to distribute only links to datasets from known sources by listing them in the datasets overview table below. You agree that any right to modify datasets originating from parties other than Megagon  are governed by the respective third party’s license conditions. 
You agree that Megagon grants no license as to any of its intellectual property and patent rights.  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS (INCLUDING MEGAGON) “AS IS” AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. You agree to cease using and distributing any part of the provided materials if you do not agree with the terms or the lack of any warranty herein.
While Megagon makes commercially reasonable efforts to ensure that citations in this document are complete and accurate, errors may occur. If you see any error or omission, please help us improve this document by sending information to contact_oss@megagon.ai.

All open source software components used within the product are listed below (including their copyright holders and the license information).
For OSS components having different portions released under different licenses, please refer to the included Upstream link(s) specified for each of the respective OSS components for identifications of code files released under the identified licenses.

| ID  | OSS Component Name | Modified | Copyright Holder | Upstream Link | License  |
|-----|----------------------------------|----------|------------------|-----------------------------------------------------------------------------------------------------------|--------------------|
| 01 | pandas | No  | AQR Capital Management, LLC, Lambda Foundry, Inc. and PyData Development Team | [link](https://pandas.pydata.org/) | BSD 3-Clause License |
| 02 | tqdm | No  | Noamraph and tqdm developers | [link](https://tqdm.github.io/) | MIT License, Mozilla Public License 2.0 |
| 03 | httpx | No  | Encode OSS Ltd. | [link](https://github.com/encode/httpx) | BSD 3-Clause License |
| 04 | nest_asyncio | No  | Ewald de Wit | [link](https://github.com/erdewit/nest_asyncio) | BSD 3-Clause License |
| 05 | websockets | No  | Aymeric Augustin and contributors | [link](https://github.com/python-websockets/websockets) | BSD 3-Clause License |
| 06 | openai | No  | OpenAI | [link](https://github.com/openai/openai-python) | Apache License Version 2.0 |
| 07 | Jsonschema | No  | Julian Berman | [link](https://github.com/python-jsonschema/jsonschema) | MIT License |
| 08 | notebook | No  | Jupyter Development Team | [link](https://github.com/jupyter/notebook) | BSD 3-Clause License |
| 09 | traitlets | No  | IPython Development Team | [link](https://github.com/ipython/traitlets) | BSD 3-Clause License |
| 10 | pydash | No  | Derrick Gilland | [link](https://github.com/dgilland/pydash) | MIT License |
| 11 | tabulate | No  | Sergey Astanin and contributors | [link](https://github.com/astanin/python-tabulate) | MIT License |
| 12 | jaro-winkler | No  | Free Software Foundation, Inc. | [link](https://github.com/richmilne/JaroWinkler.git) | GPL 3.0 License |
