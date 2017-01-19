"""
Remote control for Sony TVs
"""
## how to use
## python -c "execfile('main.py'); command('http://127.0.0.1', 'Home')"
## python main.py command('')

import os
import logging
import uuid
import json
import requests

logging.basicConfig(filename='SonyTV.log', level=logging.DEBUG)

APP_NAME = "Sony TV Client for Vera"

def command(host, command_names):
    """
    Sends the given command to the TV

    @param host: the host name or IP of the TV
    @param auth_token: the authorisation token
    @param command_names: the command or array of commands to send - see COMMANDS const for options
    """

    cookie = __setting_get("cookie")
    if not cookie:
        raise Exception("Pairing required")

    if not isinstance(command_names, list):
        command_names = [command_names]

    for command_name in command_names:
        if not command_name in COMMANDS.keys():
            raise Exception("Invalid command '{0}'".format(command_name))

    for command_name in command_names:
        data = ("""<?xml version="1.0"?>
                <SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" 
                SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
                <SOAP-ENV:Body>
                <m:X_SendIRCC xmlns:m="urn:schemas-sony-com:service:IRCC:1">
                <IRCCCode xmlns:dt="urn:schemas-microsoft-com:datatypes" 
                dt:dt="string">{command_name}</IRCCCode>
                </m:X_SendIRCC>
                </SOAP-ENV:Body>
                </SOAP-ENV:Envelope>"""
               ).format(command_name=COMMANDS[command_name])

        headers = {
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': '"urn:schemas-sony-com:service:IRCC:1#X_SendIRCC"',
            'Cookie': cookie
        }

        __post("http://{0}/sony/IRCC".format(host),
               data=data,
               headers=headers)

def pair_request(host):
    """
    Sends a pairing request to the TV. This will force the TV to displaying a
    pairing code on the screen which can be used when calling the pair method

    @param host: the host name or IP of the device
    """
    cookie = __pair(host)
    if not cookie is None:
        raise Exception("Already paired")

def pair(host, code):
    """
    Pairs the client to the TV. Requires the code that was displayed on the TV
    screen after using the pair_request method

    @param host: the host name or IP of the device
    @param code: the code displayed on the TV when calling pair_request
    """
    __pair(host, code)

def __pair(host, code=None):
    client_id = __get_client_id()

    data = ('{'
            '"id":13,'
            '"method":"actRegister",'
            '"version":"1.0",'
            '"params":[{"clientid":"iViewer:' + client_id + '","nickname":"' + APP_NAME + '"},'
            '[{"clientid":"iViewer:' + client_id + '","value":"yes","nickname":"' +
            APP_NAME + '","function":"WOL"}]]'
            '}'
           )

    headers = {
        'User-Agent' : APP_NAME + '/1',
        'Content-Type': 'application/json'
    }

    auth = ""
    if not code is None:
        auth = "user:" + code + '@'

    response = __post("http://{0}{1}/sony/accessControl".
                      format(auth, host),
                      data=data,
                      headers=headers,
                      expected_statuses=[200, 401])

    cookie = None
    if 'set-cookie' in response.headers.keys():
        cookie = response.headers['set-cookie']

    if cookie:
        __setting_set("cookie", cookie)

    return cookie

def __post(url, data, headers, expected_statuses=None):
    if expected_statuses is None:
        expected_statuses = [200]

    logging.debug('Request URL=' + url)
    logging.debug('Request Body=' + data)
    logging.debug('Request Headers=' + str(headers))
    response = requests.post(url, data=data, headers=headers)
    logging.debug('Response=' + str(response))
    logging.debug('Response Headers=' + str(response.headers))

    if expected_statuses and not response.status_code in expected_statuses:
        logging.error('Unexpected Response Code=' + str(response))
        raise Exception("Unexpected response code " + str(response.status_code))

    return response

def __settings_load():
    if os.path.isfile("settings.json"):
        with open("settings.json") as settings_file:
            settings = json.load(settings_file)
            return settings
    else:
        return {}

def __settings_save(settings):
    with open("settings.json", "w") as settings_file:
        json.dump(settings, settings_file)

def __setting_get(setting, default_value=None):
    value = default_value
    settings = __settings_load()
    if settings and setting in settings:
        value = settings[setting]
    else:
        value = default_value
    return value

def __setting_set(setting, value):
    settings = __settings_load()
    settings[setting] = value
    __settings_save(settings)

def __get_client_id():
    """ Returns a unique id of the current client - Creates one if none has been created before """
    client_id = __setting_get("client_id")
    if client_id is None:
        client_id = uuid.uuid4().hex
        __setting_set("client_id", client_id)
    return client_id

COMMANDS = {
    'Power Off' : 'AAAAAQAAAAEAAAAvAw==',
    'Analog': 'AAAAAgAAAHcAAAANAw==',
    'Audio': 'AAAAAQAAAAEAAAAXAw==',
    'Blue': 'AAAAAgAAAJcAAAAkAw==',
    'ChannelDown': 'AAAAAQAAAAEAAAARAw==',
    'ChannelUp': 'AAAAAQAAAAEAAAAQAw==',
    'Confirm': 'AAAAAQAAAAEAAABlAw==',
    'Display': 'AAAAAQAAAAEAAAA6Aw==',
    'Down': 'AAAAAQAAAAEAAAB1Aw==',
    'EPG': 'AAAAAgAAAKQAAABbAw==',
    'Exit': 'AAAAAQAAAAEAAABjAw==',
    'Forward': 'AAAAAgAAAJcAAAAcAw==',
    'Green': 'AAAAAgAAAJcAAAAmAw==',
    'Home': 'AAAAAQAAAAEAAABgAw==',
    'Input': 'AAAAAQAAAAEAAAAlAw==',
    'Left': 'AAAAAQAAAAEAAAA0Aw==',
    'Mute': 'AAAAAQAAAAEAAAAUAw==',
    'Next': 'AAAAAgAAAJcAAAA9Aw==',
    'Num0': 'AAAAAQAAAAEAAAAJAw==',
    'Num1': 'AAAAAQAAAAEAAAAAAw==',
    'Num2': 'AAAAAQAAAAEAAAABAw==',
    'Num3': 'AAAAAQAAAAEAAAADAw==',
    'Num4': 'AAAAAQAAAAEAAAADAw==',
    'Num5': 'AAAAAQAAAAEAAAAEAw==',
    'Num6': 'AAAAAQAAAAEAAAAFAw==',
    'Num7': 'AAAAAQAAAAEAAAAGAw==',
    'Num8': 'AAAAAQAAAAEAAAAHAw==',
    'Num9': 'AAAAAQAAAAEAAAAIAw==',
    'Options': 'AAAAAgAAAJcAAAA2Aw==',
    'PAP': 'AAAAAgAAAKQAAAB3Aw==',
    'Pause': 'AAAAAgAAAJcAAAAZAw==',
    'Play': 'AAAAAgAAAJcAAAAaAw==',
    'Prev': 'AAAAAgAAAJcAAAA8Aw==',
    'Red': 'AAAAAgAAAJcAAAAlAw==',
    'Return': 'AAAAAgAAAJcAAAAjAw==',
    'Rewind': 'AAAAAgAAAJcAAAAbAw==',
    'Right': 'AAAAAQAAAAEAAAAzAw==',
    'Stop': 'AAAAAgAAAJcAAAAYAw==',
    'SubTitle': 'AAAAAgAAAJcAAAAoAw==',
    'SyncMenu': 'AAAAAgAAABoAAABYAw==',
    'Up': 'AAAAAQAAAAEAAAB0Aw==',
    'VolumeDown': 'AAAAAQAAAAEAAAATAw==',
    'VolumeUp': 'AAAAAQAAAAEAAAASAw==',
    'Wide': 'AAAAAgAAAKQAAAA9Aw==',
    'Yellow': 'AAAAAgAAAJcAAAAnAw==',
    'HDMI1': 'AAAAAgAAABoAAABaAw==',
    'HDMI2': 'AAAAAgAAABoAAABbAw==',
    'HDMI3': 'AAAAAgAAABoAAABcAw==',
    'HDMI4': 'AAAAAgAAABoAAABdAw==',
    #not tested:
    'Replay': 'AAAAAgAAAJcAAAB5Aw==',
    'Advance': 'AAAAAgAAAJcAAAB4Aw==',
    'TopMenu': 'AAAAAgAAABoAAABgAw==',
    'PopUpMenu': 'AAAAAgAAABoAAABhAw==',
    'Eject': 'AAAAAgAAAJcAAABIAw==',
    'Rec': 'AAAAAgAAAJcAAAAgAw==',
    'ClosedCaption': 'AAAAAgAAAKQAAAAQAw==',
    'Teletext': 'AAAAAQAAAAEAAAA/Aw==',
    'GGuide': 'AAAAAQAAAAEAAAAOAw==',
    'DOT' : 'AAAAAgAAAJcAAAAdAw==',
    'Digital': 'AAAAAgAAAJcAAAAyAw==',
    'BS' : 'AAAAAgAAAJcAAAAsAw==',
    'CS' : 'AAAAAgAAAJcAAAArAw==',
    'BSCS': 'AAAAAgAAAJcAAAAQAw==',
    'Ddata': 'AAAAAgAAAJcAAAAVAw==',
    'InternetWidgets': 'AAAAAgAAABoAAAB6Aw==',
    'InternetVideo': 'AAAAAgAAABoAAAB5Aw==',
    'SceneSelect': 'AAAAAgAAABoAAAB4Aw==',
    'Mode3D' : 'AAAAAgAAAHcAAABNAw==',
    'iManual' : 'AAAAAgAAABoAAAB7Aw==',
    'Jump' : 'AAAAAQAAAAEAAAA7Aw==',
    'MyEPG': 'AAAAAgAAAHcAAABrAw==',
    'ProgramDescription': 'AAAAAgAAAJcAAAAWAw==',
    'WriteChapter': 'AAAAAgAAAHcAAABsAw==',
    'TrackID' : 'AAAAAgAAABoAAAB+Aw==',
    'TenKey': 'AAAAAgAAAJcAAAAMAw==',
    'AppliCast': 'AAAAAgAAABoAAABvAw==',
    'acTVila': 'AAAAAgAAABoAAAByAw==',
    'DeleteVideo': 'AAAAAgAAAHcAAAAfAw==',
    'EasyStartUp': 'AAAAAgAAAHcAAABqAw==',
    'OneTouchTimeRec': 'AAAAAgAAABoAAABkAw==',
    'OneTouchView' : 'AAAAAgAAABoAAABlAw==',
    'OneTouchRec' : 'AAAAAgAAABoAAABiAw==',
    'OneTouchRecStop' : 'AAAAAgAAABoAAABjAw==',
    }
#pair_request('192.168.188.84')
#pair('192.168.188.84', '5354')
#command('192.168.188.84', 'Home')
# print __setting_get("aaa", "bbb")
# __setting_set("aaa", "ccc")
# print __setting_get("aaa", "bbb")