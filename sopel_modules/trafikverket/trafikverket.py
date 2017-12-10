# coding=utf-8

from __future__ import unicode_literals, absolute_import, division, print_function

from sopel import module

import logging

LOG = logging.getLogger(__name__)

def configure(config):
    pass


def setup(bot):
    LOG.info('Initializing setup')
    pass


@module.commands('tåg')
def hello_world(bot, trigger):
    bot.say('Trainmessage')


@module.commands('väg')
def hello_world(bot, trigger):
    bot.say('Roadmessage')
