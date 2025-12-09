# biokb_coconut

## For impatient users

Prerequisites: git (with SSH key at GitHub), python3, podman

```bash
git clone git@github.com:biokb/biokb_coconut.git
python3 -m venv .venv
source .venv/bin/activate
pip install .
biokb-coconut import-data
biokb-coconut create-ttls
# Run Neo4j as test container
podman run --name test_neo --rm --publish=7474:7474 --publish=7687:7687 --env NEO4J_AUTH=neo4j/test_passwd neo4j
biokb-coconut import-neo4j -p test_passwd
```
Open Neo4j browser at http://localhost:7474 and login with neo4j/test_passwd

**Tipp:** Use ... to see all available commands.
1. `biokb-coconut import-data --help` 
2. `biokb-coconut create-ttls --help`
3. `biokb-coconut import-neo4j --help`

## Run fastAPI

#TODO: Fix fastAPI

start fastAPI
```bash
git clone git@github.com:biokb/biokb_coconut.git
python3 -m venv .venv
source .venv/bin/activate
pip install .
biokb-coconut import-data
fastapi run src/biokb_coconut/api/main.py --reload
```

Open http://127.0.0.1:8000/docs
