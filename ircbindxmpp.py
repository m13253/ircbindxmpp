#!/usr/bin/env python

import sleekxmpp

import config
import libirc

def getBareJID(jid):
    return jid.split('/', 1)[0]

class XMPPBot(sleekxmpp.ClientXMPP):
    def __init__(self, jid, password):
        sleekxmpp.ClientXMPP.__init__(self, jid, password)
        self.add_event_handler("session_start", self.start)
        self.add_event_handler("message", self.message)

    def start(self, event):
        self.send_presence()
        self.get_roster()

    def message(self, msg):
        if msg['type'] not in ('chat', 'normal'):
            return
        from_jid=msg['from'].bare
        for i in config.XMPP['forward']:
            if i[0]==from_jid:
                for l in msg['body'].splitlines():
                    print('< %s' % l)
                    irc.say(i[1], '(GTalk) %s' % l)

if __name__=='__main__':
    try:
        irc=libirc.IRCConnection()
        irc.connect(config.IRC['server'], config.IRC['port'])
        irc.setnick(config.IRC['nick'])
        irc.setuser()
        if config.IRC['password']:
            irc.say('NickServ', 'identify %s' % config.IRC['password'])
        for i in config.IRC['forward']:
            irc.join(i[0])
        xmpp=XMPPBot(config.XMPP['JID'], config.XMPP['password'])
        xmpp.register_plugin('xep_0030') # Service Discovery
        xmpp.register_plugin('xep_0004') # Data Forms
        xmpp.register_plugin('xep_0060') # PubSub
        xmpp.register_plugin('xep_0199') # XMPP Ping
        if xmpp.connect((config.XMPP['server'], config.XMPP['port'])):
            xmpp.process(block=False)
        else:
            irc.quit('Cannot connect to XMPP.')
            exit()
        while irc.sock:
            line=irc.parse(block=True)
            if not line:
                continue
            if line['cmd']=='PRIVMSG':
                for i in config.IRC['forward']:
                    if line['dest']==i[0]:
                        print('> %s' % line['msg'])
                        xmpp.send_message(mto=i[1], mbody='%s (IRC): %s' % (line['nick'], line['msg']), mtype='chat')
        else:
            xmpp.disconnect(wait=True)
    except KeyboardInterrupt:
        xmpp.disconnect(wait=True)
        irc.quit()

# vim: et ft=python sts=4 sw=4 ts=4
