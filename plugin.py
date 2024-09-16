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
import pprint  # For pretty printing in debug logs

class RepostCount(callbacks.Plugin):
    """
    A plugin to track and count reposts of links in a specified channel.
    """

    def __init__(self, irc):
        self.__parent = super(RepostCount, self)
        self.__parent.__init__(irc)
        self.link_database = {}  # Stores links and their original posters
        self.filename = conf.supybot.directories.data.dirize(self.name() + '.db')
        self.user_repost_count = self.load_data()  # Loads existing repost counts

    def load_data(self):
        """Load the user repost count data from a file."""
        try:
            with open(self.filename, 'r') as f:
                return eval(f.read())
        except:
            return {}  # Return an empty dict if file doesn't exist or is invalid

    def save_data(self):
        """Save the user repost count data to a file."""
        with open(self.filename, 'w') as f:
            f.write(repr(self.user_repost_count))

    def die(self):
        """Save data when the plugin is unloaded."""
        self.save_data()
        self.__parent.die()

    def _strip_url_params(self, url):
        """Remove query parameters from a URL."""
        parsed = urlparse(url)
        clean_url = urlunsplit((parsed.scheme, parsed.netloc, parsed.path, '', ''))
        return clean_url

    def _extract_url(self, text):
        """Extract the first URL from a given text."""
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        match = re.search(url_pattern, text)
        return match.group(0) if match else None

    def _purge_old_links(self):
        """Remove links older than 12 hours from the database."""
        current_time = time.time()
        old_links = [url for url, (_, timestamp) in self.link_database.items() 
                     if current_time - timestamp > 12 * 3600]
        for url in old_links:
            del self.link_database[url]

    def doPrivmsg(self, irc, msg):
        """Handle incoming messages and check for reposts."""
        channel = msg.args[0]
        self.log.debug(f"Processing message in channel: {channel}")
        
        if irc.isChannel(channel) and channel == self.registryValue('channel'):
            text = msg.args[1]
            url = self._extract_url(text)
            
            if url:
                self._purge_old_links()
                clean_url = self._strip_url_params(url)
                nick = msg.nick
                current_time = time.time()

                if clean_url in self.link_database:
                    original_poster, post_time = self.link_database[clean_url]
                    
                    if nick != original_poster:
                        time_diff = current_time - post_time
                        hours, remainder = divmod(time_diff, 3600)
                        minutes, _ = divmod(remainder, 60)
                        
                        self.user_repost_count[nick] = self.user_repost_count.get(nick, 0) + 1
                        
                        irc.reply(f"That link was already posted by {original_poster} {int(hours)}h {int(minutes)}m ago. Repost count for {nick} is now {self.user_repost_count[nick]}.", prefixNick=False)
                    else:
                        self.link_database[clean_url] = (nick, current_time)
                else:
                    self.link_database[clean_url] = (nick, current_time)

                self.save_data()

        # Debug logging (only once per message processing)
        self.log.debug(f"link_database: {pprint.pformat(self.link_database)}")
        self.log.debug(f"user_repost_count: {pprint.pformat(self.user_repost_count)}")

    def reposters(self, irc, msg, args):
        """takes no arguments

        Shows the top 15 reposters leaderboard.
        """
        if not self.user_repost_count:
            irc.reply("No reposts have been recorded yet.")
            return

        # Sort users by repost count in descending order
        sorted_reposters = sorted(self.user_repost_count.items(), key=lambda x: x[1], reverse=True)

        # Get the top 15 reposters
        top_reposters = sorted_reposters[:15]

        # Format the leaderboard
        leaderboard = ["Top 15 Reposters:"]
        for user, count in top_reposters:
            leaderboard.append(f"{user}:{count}")

        # Join the leaderboard entries and reply
        irc.reply(" ".join(leaderboard), prefixNick=False)

    reposters = wrap(reposters)

Class = RepostCount

# Register the plugin
conf.registerPlugin('RepostCount')
conf.registerChannelValue(conf.supybot.plugins.RepostCount, 'channel',
    registry.String('', """The channel where the RepostCount should be active."""))
