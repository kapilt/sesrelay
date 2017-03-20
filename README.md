# SMTP 2 SES Message Relay

Trivial twisted program that provides smtp server
that delivers messages via ses api, based on sample
smtp server tac.

This is intended for low volume usage from machines
without direct internet access but can reach ses
api endpoints via proxy.


# Running it

```shell

git checkout https://github.com/kapilt/sesrelay.git
virtualenv sesrelay
source sesrelay/bin/activate
pip install -r sesrelay/requirements.txt
twistd -y sesrelay/sesrelay.py
```

requires mods for port/region
