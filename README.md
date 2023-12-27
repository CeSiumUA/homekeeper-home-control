# home-control

This repo is a part of my HomeKeeper project.
It is has several features, to make my home smarter.
Home control has several features:

1. Throw events timing via MQTT. Currently there are 4 main types of events: Sunrise, Sunset, Wake-up time, Bed time. There is also support for Custom events (but without a handler as for now)
2. Throw events via MQTT and telegram bot if a specific device is connected/disconnected from home network
3. Handle commands via telegram bot
4. Notify ip address changed with the help of [homekeeper-link-client](https://github.com/CeSiumUA/homekeeper-link-client)
5. Download video from YouTube using [homekeeper-youtube](https://github.com/CeSiumUA/homekeeper-youtube)
6. Collect data from smart devices in my home (currently only Tasmota), and control these devices over MQTT

## HomeKeeper projects

List of all HomeKeeper micro-projects

1. (**Discontinued**) [horizon-hues](https://github.com/CeSiumUA/homekeeper-horizon-hues) (**project moved to this repo, and is now a part of home-control**) - sunset and sunrise MQTT notifier.
2. (**Discontinued**) [netwatcher](https://github.com/CeSiumUA/homekeeper-netwatcher) (**project moved to this repo, and is now a part of home-control**) - device network connection/disconnection MQTT notifier.
3. (**Discontinued**) [telegram-bot](https://github.com/CeSiumUA/homekeeper-telegram-bot) (**project moved to this repo, and is now a part of home-control**) - telegram bot messages handler, routes messages from bot to MQTT and other HomeKeeper parts. 
P.S. Not the best demonstration of code quality, tbh, as it was one of my first experiences with python :)
4. [youtube](https://github.com/CeSiumUA/homekeeper-youtube) - YouTube video downloader. Pretty undeveloped, saves video locally, and needs to be updated as YouTube can block the functionality of underlying library
5. [link-client](https://github.com/CeSiumUA/homekeeper-link-client) - A client which periodically performs "alive" signal transmission to `link-server`. Detailed below
6. [link-server](https://github.com/CeSiumUA/homekeeper-link-server) - A server, listens to link-client "alive" transmission and notifies a HomeKeeper user via telegram bot, if link-client is down. Very useful during frequent blackouts.
7. [compose](https://gist.github.com/CeSiumUA/6c2a59e5b0468946eb763e900c4c8569) - this is link to docker-compose file in Gist. The full project with all submodules is hosted on my own git server, so you'll just need to git clone every repository above, and download a compose file.

## How to run HomeKeeper?

To run HomeKeeper, create a folder, and run the following commands:

```
git clone https://github.com/CeSiumUA/homekeeper-youtube
```

```
git clone https://github.com/CeSiumUA/homekeeper-link-client
```

```
wget https://gist.githubusercontent.com/CeSiumUA/6c2a59e5b0468946eb763e900c4c8569/raw/f12e0bc49ecb45ecfb1a03eb135de50f21cd8a04/docker-compose.yaml
```

Discontinued:
```
git clone https://github.com/CeSiumUA/homekeeper-horizon-hues
```

```
git clone https://github.com/CeSiumUA/homekeeper-netwatcher
```

```
git clone https://github.com/CeSiumUA/homekeeper-telegram-bot
```

The next step, is to configure `link-client` and `netwatcher` (discontinued), see the corresponding repositories for details.

Afterwards, you should create a .env file, see `docker-compose.yaml` for required variables.

Finally, run:

```
docker-compose build
```

```
docker-compose up -d
```

Now, HomeKeeper should run!
