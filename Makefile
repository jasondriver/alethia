lib:
	cd alethia_tp; make

tp:
	cp alethia_tp/alethia_tp-0.0.1-py3-none-any.whl alethia_component/
	cd alethia_component; make

rsyslog:
	cp submitter.py rsyslog_client/
	cd rsyslog_client; make

up: tp rsyslog
	docker-compose -f sawtooth-default.yaml up &

down:
	docker-compose -f sawtooth-default.yaml down

all: lib tp rsyslog

.PHONY: all run tp lib down
