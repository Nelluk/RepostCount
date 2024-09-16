import supybot.utils as utils
from supybot.commands import *
import supybot import plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import supybot.ircmsgs as ircmsgs
import supybot.conf as conf
import supybot.world as world
import time
import re
from urllib.parse import urlparse, urlunsplit

class RepostCounter(callbacks.Plugin):
    def __init__(self, irc):
        self.__parent = super(RepostCounter, self)
        self.__parent.__init__(irc)
        self.link_database = {}
        self.filename = conf.supybot.directories.data.dirize(self.name() + '.db')
        self.user_repost_count = self.load_data()

    def load_data(self):
        try:
            with open(self.filename, 'r') as f:
                return eval(f.read())
        except:
            return {}

    def save_data(self):
        with open(self.filename, 'w') as f:
            f.write(repr(self.user_repost_count))

    def die(self):
        self.save_data()
        self.__parent.die()

    def _strip_url_params(self, url):
        parsed = urlparse(url)
        clean_url = urlunsplit((parsed.scheme, parsed.netloc, parsed.path, '', ''))
        return clean_url

    def _extract_url(self, text):
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        match = re.search(url_pattern, text)
        return match.group(0) if match else None

    def _purge_old_links(self):
        current_time = time.time()
        old_links = [url for url, (_, timestamp) in self.link_database.items() 
                     if current_time - timestamp > 12 * 3600]
        for url in old_links:
            del self.link_database[url]

    def doPrivmsg(self, irc, msg):
        channel = msg.args[0]
        if irc.isChannel(channel) and channel == self.registryValue('channel'):
            text = msg.args[1]
            url = self._extract_url(text)
            if url:
                self._purge_old_links()
                clean_url = self._strip_url_params(url)
                nick = msg.nick
                current_time = time.time()

                if clean_url in self.link_database:
                    prev_nick, prev_timestamp = self.link_database[clean_url]
                    hours_ago = (current_time - prev_timestamp) / 3600
                    
                    if hours_ago <= 12:
                        self.user_repost_count[nick] = self.user_repost_count.get(nick, 0) + 1
                        self.save_data()  # Save after updating the count
                        
                        response = f"You just reposted {prev_nick}'s link from {hours_ago:.1f} hours ago. "
                        response += f"You have reposted {self.user_repost_count[nick]} links."
                        
                        irc.reply(response, prefixNick=False)
                    else:
                        # Update the link with the new timestamp and nick
                        self.link_database[clean_url] = (nick, current_time)
                else:
                    self.link_database[clean_url] = (nick, current_time)

Class = RepostCounter

conf.registerPlugin('RepostCounter')
conf.registerChannelValue(conf.supybot.plugins.RepostCounter, 'channel',
    registry.String('', """The channel where the RepostCounter should be active."""))
