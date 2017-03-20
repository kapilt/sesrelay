# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

# Based on 
# http://twistedmatrix.com/documents/current/_downloads/emailserver.tac
# https://github.com/twisted/twisted/blob/trunk/LICENSE

"""
send messages received over smtp via ses api
"""

from __future__ import print_function

from zope.interface import implementer

from twisted.internet import defer
from twisted.mail import smtp
from twisted.mail.imap4 import LOGINCredentials, PLAINCredentials

from twisted.cred.checkers import InMemoryUsernamePasswordDatabaseDontUse
from twisted.cred.portal import IRealm
from twisted.cred.portal import Portal

import boto3
import logging


def send_message(msg):
    session = boto3.Session()
    client = session.client('ses', region_name='us-east-1')
    try:
        client.send_raw_email(RawMessage={'Data': msg})
    except Exception as e:
        logging.error("Err sending email: %s" % e)
        return False
    return True


@implementer(smtp.IMessageDelivery)
class RelayMessageDelivery:
    def receivedHeader(self, helo, origin, recipients):
        return "Received: MessageDelivery"

    def validateFrom(self, helo, origin):
        # All addresses are accepted
        return origin

    def validateTo(self, user):
        return lambda: RelayMessage()


@implementer(smtp.IMessage)
class RelayMessage:
    def __init__(self):
        self.lines = []

    def lineReceived(self, line):
        self.lines.append(line)

    def eomReceived(self):
        from twisted.internet import threads
        print("New message received:")
        msg = "\n".join(self.lines)
        self.lines = None
        return threads.deferToThread(send_message, msg)

    def connectionLost(self):
        # There was an error, throw away the stored lines
        self.lines = None


class SESRelaySMTPFactory(smtp.SMTPFactory):
    protocol = smtp.ESMTP

    def __init__(self, *a, **kw):
        smtp.SMTPFactory.__init__(self, *a, **kw)
        self.delivery = RelayMessageDelivery()

    def buildProtocol(self, addr):
        p = smtp.SMTPFactory.buildProtocol(self, addr)
        p.delivery = self.delivery
        p.challengers = {"LOGIN": LOGINCredentials, "PLAIN": PLAINCredentials}
        return p


@implementer(IRealm)
class SimpleRealm:
    def requestAvatar(self, avatarId, mind, *interfaces):
        if smtp.IMessageDelivery in interfaces:
            return smtp.IMessageDelivery, RelayMessageDelivery(), lambda: None
        raise NotImplementedError()


def main():
    from twisted.application import internet
    from twisted.application import service

    portal = Portal(SimpleRealm())
    checker = InMemoryUsernamePasswordDatabaseDontUse()
    checker.addUser("guest", "guest")
    portal.registerChecker(checker)

    app = service.Application("SES Relay SMTP Server")
    internet.TCPServer(8080, SESRelaySMTPFactory(portal)).setServiceParent(app)

    return app

application = main()
