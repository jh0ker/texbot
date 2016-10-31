# TexBot
#### A Python Telegram Bot that converts LaTeX markup into an image

It uses the Flask microframework and the [python-telegram-bot](https://github.com/leandrotoledo/python-telegram-bot) library. 
It's based on this [example](https://github.com/sooyhwang/Simple-Echo-Telegram-Bot), uses a slightly modified version of [this perl script](http://www.fourmilab.ch/webtools/textogif/) and [pickledb](https://bitbucket.org/patx/pickledb) for basic persistence.

Please also check out my other bots, [GitBot](https://github.com/jh0ker/gitbot) and [Welcome Bot](https://github.com/jh0ker/welcomebot).

The file is prepared to be run by anyone by filling out the blanks in the configuration. The bot currently runs on [@jh0ker_texbot](https://telegram.me/jh0ker_texbot)

## Required
* Python 3.5 (may work with earlier versions, untested)
* [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) module (tested with version 5.2.0)
* [ImageMagick](http://www.imagemagick.org/script/index.php) (tested with version 6.7.2-7)

You also need to fulfill the perl scripts' requirements, found at the bottom of [it's page at fourmilab.ch](http://www.fourmilab.ch/webtools/textogif/)

## How to use
* Install the script
* Edit TOKEN bot.py
* Follow Bot instructions
