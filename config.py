import toml
global config
config = {}

def Load():
    global config
    try:
        with open('config.toml') as toml_config:
            config = toml.load(toml_config)
    except OSError:
        print("> Unable to find config, using default")

        with open('config.example.toml') as toml_config:
            config = toml.load(toml_config)

    assert config != {}, "No config, unable to continue"
