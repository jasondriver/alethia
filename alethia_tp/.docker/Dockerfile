FROM ubuntu

RUN apt-get update

RUN apt-get install -y wget
RUN mkdir -p /etc/pki/tls/certs
RUN wget https://curl.haxx.se/ca/cacert.pem
RUN mv cacert.pem /etc/pki/tls/certs/ca-bundle.crt

RUN apt-get install -y python3 python3-pip
RUN pip3 install wheel
