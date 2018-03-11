# coding=utf-8

from __future__ import unicode_literals, absolute_import, division, print_function
from sopel import module
from sopel.config import ConfigurationError
from xml.etree import ElementTree as ET

import requests
import configparser

API_XML_ENPOINT = 'http://api.trafikinfo.trafikverket.se/v1.3/data.xml'

auth_key      = ''
train_trigger = 'tåg'
road_trigger  = 'vag'


def xml_request_body(object_type, include_fields):

    xml_root   = ET.Element('REQUEST')
    login_tag  = ET.SubElement(xml_root, 'LOGIN')
    query_tag  = ET.SubElement(xml_root, 'QUERY')
    filter_tag = ET.SubElement(query_tag,'FILTER')

    for field in include_fields:
        include_tag = ET.SubElement(query_tag, 'INCLUDE')
        include_tag.text = str(field)

    login_tag.set('authenticationkey', str(auth_key))
    query_tag.set('objecttype', str(object_type))
    query_tag.set('limit', '3')

    str(ET.tostring(xml_root, encoding='utf-8', method='xml'))
    return ET.tostring(xml_root, encoding='utf-8', method='xml')


def send_request(payload):

    headers = {'Content-Type': 'text/xml'}

    try:
        response = requests.post(API_XML_ENPOINT, data=payload, headers=headers)
    except Exception:
        return 'API request failed'

    if (response.status_code == 200):
        return response

    return 'Error HTTP Status Code ' + response.status_code


def build_header(header_items):

    header = ''

    for item in header_items:
        header = header + '[' + item + ']'

    return header

import logging

LOG = logging.getLogger(__name__)

def configure(config):
    pass


def setup(bot):

    config = configparser.ConfigParser()
    config.read('config.ini')

    if not config.has_option('auth', 'auth_key'):
        raise ConfigurationError('No authentication key for Trafikverket API provided in config.ini')

    global auth_key
    auth_key = config.get('auth', 'auth_key')

    if config.has_option('triggers', 'road_trigger'):
        global road_trigger
        road_trigger = config.get('triggers', 'road_trigger')


@module.commands(train_trigger)
def train_command(bot, trigger):

    request_body = xml_request_body('TrainMessage',
                                    ['Header',
                                    'StartDateTime',
                                    'LastUpdateDateTime',
                                    'ExternalDescription',
                                    'ReasonCodeText',
                                    'Geometry.WGS84'])

    bot.say(request_body)
    response = send_request(request_body)
    bot.say(response.content)


@module.commands('väg')
def hello_world(bot, trigger):
    bot.say(road_trigger)
    bot.say(trigger)
