# Use the Sawtooth intkey-tp image as a base
FROM hyperledger/sawtooth-intkey-tp-python:1.0

RUN apt-get update
RUN apt-get install -y python3-pip
RUN pip3 install --upgrade pip

WORKDIR /home/sawtooth
ADD alethia_tp-0.0.1-py3-none-any.whl /home/sawtooth

RUN pip3 install alethia_tp-0.0.1-py3-none-any.whl
