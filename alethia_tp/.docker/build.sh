#!/bin/sh
docker run --rm -i --user="$(id -u):$(id -g)" -v $PWD:/build -w /build alethia-build pip3 wheel .
