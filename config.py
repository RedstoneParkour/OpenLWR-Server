import json

global config
config = {}

def Load():
    global config
    try:
        with open('config.json') as json_config:
            config = json.load(json_config)
    except OSError:
        print("> Unable to find config, using default")

        with open('config.example.json') as json_config:
            config = json.load(json_config)

    assert config != {}, "No config, unable to continue"
