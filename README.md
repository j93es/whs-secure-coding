# Secure Coding

## Tiny Secondhand Shopping Platform.

You should add some functions and complete the security requirements.

## requirements

If you don't have a miniconda(or anaconda), you can install it on this url. - https://docs.anaconda.com/free/miniconda/index.html

```
git clone https://github.com/j93es/whs-assignment.git
cd ./secure-coding/secure-coding
conda env create -f enviroments.yaml --name secure-coding
conda activate secure-coding
```

## Usage

### dotenv

Config your .env in root dir(./)

```text
ENV=production
ADMIN_JWT_SECRET_KEY=
CLIENT_JWT_SECRET_KEY=
SECRET_KEY=
ADMIN_ID=
ADMIN_PW=
```

### init DB

Run this script to initialize the database.

```sh
cd ./src
python app.py
```

### deploy.sh

Configure the port to run.

```sh
#!/bin/bash

PORT=8080
...
```

### HTTPS, WSS

This app uses HTTPS by default. Use a reverse proxy manager such as nginx or apache to obtain a certificate using certbot, etc., and operate the service in a safe environment.

### deploy

run the server process.

```
chmod +x deploy.sh
./deploy.sh
```

### security update

If you want check security update, you can use `pip-audit` command

```sh
pip-audit
```
