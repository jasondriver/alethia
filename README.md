# Project Alethia #

A distributed, blockchain based solution for guaranteeing system log integrity.
Stores sha256 hashes of each log line onto the sawtooth blockchain, verifier
pulls a page of hashes and outputs the line number of mutated log entries in
the original log file.

## ECS 251 Notes
We wrote everything in this repository, with two exceptions. First,
`sawtooth-default.yaml` was provided by the Docker-based distribution for
Hyperledger Sawtooth. We modified it to include our own Alethia transaction
processor container, which is based off of the IntKey Docker image (see
`alethia_component/Dockerfile`). Second, we used the `sawtooth-intkey` Python
package as a base for our Alethia module. We carved out almost all of the existing
code, but some glue remains, notably the CLI wrapper `alethia_tp/alethia_tp/processor/main.py`.
The main file of note in `alethia_tp/` is `processor/handler.py`, which implements
the logic for the Alethia transaction family proper.

## Getting Started
Sets up the docker containers containing sawtooth and the alethia TP.  See
__main__ for examples on how to append to the blockchain and verify.

## Prerequisites
```
docker >= 17.03.0-ce
docker-compose >= 2.0
```

## Installing
```
# Sign in to the terminal on a working linux system
git clone https://gitlab.com/ecs-251-alethia/alethia.git
cd alethia
make all
# Run docker-compose
make up
```

## Running the tests
```
git pull https://gitlab.com/ecs-251-alethia/alethia.git
cd alethia
make all
make up
# In another terminal run
docker exec -it sawtooth-shell-default bash # to connect to the client container
# once inside client container run
apt update && apt upgrade && apt install vim
# then copy n paste a submitter.py, verifier.py
mkdir test_case_logs && cd test_case_logs
# copy and paste test examples as foo.log
cd ..
python3 verifier.py
```
