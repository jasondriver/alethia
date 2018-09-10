FROM hyperledger/sawtooth-all:1.0

ADD 60-alethia.conf /etc/rsyslog.d/
ADD submitter.py /opt/
ADD alethia-logger /opt/

RUN apt-get update
RUN apt-get install -y rsyslog
# RUN service rsyslog start

CMD bash
