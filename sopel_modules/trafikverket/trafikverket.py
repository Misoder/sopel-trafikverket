# coding=utf-8

from __future__ import unicode_literals, absolute_import, division, print_function

from sopel import module
from sopel.config import ConfigurationError
from sopel.formatting import *

from xml.etree import ElementTree as ET

import requests
import configparser
import urllib.parse
import json

API_XML_ENPOINT = 'http://api.trafikinfo.trafikverket.se/v1.3/data.xml'

trfv_auth_key  = None
google_api_key = None
train_trigger  = 'tåg'
road_trigger   = 'road'


def xml_request_body(object_type, fields, order_by='LastUpdateDateTime desc', limit=3):

    xml_root   = ET.Element('REQUEST')
    login_tag  = ET.SubElement(xml_root, 'LOGIN')
    query_tag  = ET.SubElement(xml_root, 'QUERY')
    ET.SubElement(query_tag, 'FILTER')

    for field in fields:
        include_tag = ET.SubElement(query_tag, 'INCLUDE')
        include_tag.text = str(field)

    login_tag.set('authenticationkey', str(trfv_auth_key))
    query_tag.set('objecttype',        str(object_type))
    query_tag.set('orderby',           order_by)
    query_tag.set('limit',             str(limit))

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

    return 'Error HTTP Status Code ' + str(response.status_code)


def google_maps_url(lat, long):

    global google_api_key

    url      = 'https://www.google.se/maps/search/?api=1&'
    params   = {'query': str(lat) + ',' + str(long)}
    maps_url = url + urllib.parse.urlencode(params)

    if google_api_key is not None:
        api_shortener = 'https://www.googleapis.com/urlshortener/v1/url' + '?key=' + google_api_key
        headers = {'Content-Type': 'application/json'}
        json_body = {}
        json_body['longUrl'] = maps_url
        response = requests.post(api_shortener, data=json.dumps(json_body), headers=headers)
        json_response = json.loads(response.text)
        return json_response.get('id', maps_url)
    else:
        return maps_url


def configure(config):
    pass


def setup(bot):

    config = configparser.ConfigParser()
    config.read('config.ini')

    if not config.has_option('auth', 'trfv_auth_key'):
        raise ConfigurationError('No authentication key for Trafikverket API provided in config.ini')

    global trfv_auth_key
    trfv_auth_key = config.get('auth', 'trfv_auth_key')

    if config.has_option('triggers', 'road_trigger'):
        global road_trigger
        road_trigger = config.get('triggers', 'road_trigger')

    if config.has_option('auth', 'google_api_key'):
        global google_api_key
        google_api_key= config.get('auth', 'google_api_key')

@module.commands(train_trigger)
def train_command(bot, trigger):

    request_body = xml_request_body('TrainMessage',
                                    ['Header',
                                    'StartDateTime',
                                    'LastUpdateDateTime',
                                    'ExternalDescription',
                                    'ReasonCodeText',
                                    'Geometry.WGS84'])

    response     = send_request(request_body)
    xml_response = ''
    irc_string   = ''

    try:
        xml_response = ET.fromstring(response.text)
    except Exception:
        bot.say('Failed to parse response. :\'( ')
        return

    for xml_result in xml_response:
        for xml_trainmessage in xml_result:

            if xml_trainmessage.find('StartDateTime') is not None:
                irc_string = color(('[' + xml_trainmessage.find('StartDateTime').text[:-3] + ']').replace('T', ' '), colors.YELLOW)
            if xml_trainmessage.find('LastUpdateDateTime') is not None:
                irc_string += color(('[Uppdaterad ' + xml_trainmessage.find('LastUpdateDateTime').text[:-3] + ']').replace('T', ' '), colors.LIGHT_GREEN)
            if xml_trainmessage.find('ReasonCodeText') is not None:
                irc_string += bold(('[' + xml_trainmessage.find('ReasonCodeText').text + ']'))

            bot.say(irc_string)

            if xml_trainmessage.find('ExternalDescription') is not None:
                bot.say(xml_trainmessage.find('ExternalDescription').text)
            else:
                bot.say('No further information available')

            if xml_trainmessage.find('Geometry') is not None:
                geo = xml_trainmessage.find('Geometry').find('WGS84').text
                geo = geo[geo.find('(')+1:geo.find(')')].split(' ')
                bot.say(color(google_maps_url(geo[1], geo[0]), colors.GRAY))


@module.commands(road_trigger)
def hello_world(bot, trigger):
    bot.say(road_trigger)
    bot.say(trigger)
