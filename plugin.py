import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import supybot.ircmsgs as ircmsgs
import supybot.conf as conf
import supybot.world as world
import time
import re
from urllib.parse import urlparse, urlunsplit
from supybot import registry
import pprint  # Add this import for pretty printing

class RepostCount(callbacks.Plugin):
    def __init__(self, irc):
        self.__parent = super(RepostCount, self)
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
        self.log.debug(f"Processing message in channel: {channel}")
        self.log.debug(f"Registry channel value: {self.registryValue('channel')}")
        
        if irc.isChannel(channel) and channel == self.registryValue('channel'):
            text = msg.args[1]
            url = self._extract_url(text)
            self.log.debug(f"Extracted URL: {url}")
            
            if url:
                self._purge_old_links()
                clean_url = self._strip_url_params(url)
                nick = msg.nick
                current_time = time.time()

                self.log.debug(f"Clean URL: {clean_url}")
                self.log.debug(f"Nick: {nick}")
                self.log.debug(f"Current time: {current_time}")

                # Debug log: Print the current link_database
                self.log.debug("Current link_database:")
                self.log.debug(pprint.pformat(self.link_database))

                # Debug log: Print the current user_repost_count
                self.log.debug("Current user_repost_count:")
                self.log.debug(pprint.pformat(self.user_repost_count))

                if clean_url in self.link_database:
                    self.log.debug(f"URL found in link_database")
                    original_poster, post_time = self.link_database[clean_url]
                    self.log.debug(f"Original poster: {original_poster}, Post time: {post_time}")
                    
                    if nick != original_poster:
                        self.log.debug(f"Repost detected")
                        time_diff = current_time - post_time
                        hours, remainder = divmod(time_diff, 3600)
                        minutes, _ = divmod(remainder, 60)
                        
                        self.user_repost_count[nick] = self.user_repost_count.get(nick, 0) + 1
                        
                        irc.reply(f"{nick}: That link was already posted by {original_poster} {int(hours)} hours and {int(minutes)} minutes ago.")
                        irc.reply(f"Your repost count is now {self.user_repost_count[nick]}.")
                        
                        # Debug log: Print updated user_repost_count after increment
                        self.log.debug("Updated user_repost_count after increment:")
                        self.log.debug(pprint.pformat(self.user_repost_count))
                    else:
                        self.log.debug(f"Same user posted the link again")
                        self.link_database[clean_url] = (nick, current_time)
                else:
                    self.log.debug(f"New URL added to link_database")
                    self.link_database[clean_url] = (nick, current_time)

                # Debug log: Print final link_database after processing
                self.log.debug("Final link_database after processing:")
                self.log.debug(pprint.pformat(self.link_database))

                self.save_data()
        else:
            self.log.debug(f"Message not processed: channel mismatch or not a channel message")

    def die(self):
        self.save_data()
        self.__parent.die()

Class = RepostCount

conf.registerPlugin('RepostCount')
conf.registerChannelValue(conf.supybot.plugins.RepostCount, 'channel',
    registry.String('', """The channel where the RepostCount should be active."""))
