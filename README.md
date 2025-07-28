# biokb_coconut

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Run with MySQL

**Requirements:**
- podman

install podman-compose
```bash
pip install podman-compose
```

set connection for fastAPI
```bash
export CONNECTION_STR="mysql+pymysql://biokb_user:biokb_passwd@127.0.0.1:3307/biokb"
```

start MySQL (port:3307) and phpMyAdmin(port:8081) as container 

```bash
podman-compose up -d mysql pma
```

start fastAPI
```bash
fastapi run src/biokb_coconut/api/main.py --reload
```

Open http://127.0.0.1:8000/docs
