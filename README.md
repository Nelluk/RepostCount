# RepostCount Plugin for Limnoria

## Description

RepostCount is a plugin for the Limnoria IRC bot that tracks and counts reposts of links in a specified channel. It helps maintain channel quality by alerting users when they post links that have already been shared.

## Features

- Tracks posted links in a specified channel
- Detects when a link is reposted
- Counts the number of reposts per user
- Ignores query parameters in URLs to avoid false positives
- Automatically purges links older than 12 hours from its database

## Installation

1. Copy the `RepostCount` folder to your Limnoria plugins directory.
2. Load the plugin:
   ```
   @load RepostCount
   ```

## Configuration

Before using the plugin, you need to set the channel where it should be active:

```
@set RepostCount.channel #yourchannel
```

## Usage

- The plugin will automatically track links posted in the specified channel.
- It will reply to each link with the number of reposts it has received.

## License

This plugin is licensed under the MIT License.