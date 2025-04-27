from simulation.constants.annunciator_states import AnnunciatorStates
import math

alarms = {
    "test_alarm" : {
        "alarm" : False,
        "box": "Box1",
		"window": "1-2",
        "state" : AnnunciatorStates.CLEAR,
        "group" : "1",
        "silenced" : False,
    },
}

switches = {
    "test_switch": {
        "positions": {
			0: 45,
			1: 0,
			2: -45,
		},
        "position": 0,
        "lights" : {     
            "green" : True,
            "red" : False,
        },
        "flag" : "green",
        "momentary" : False,
    },
    "test_switch2": {
        "positions": {
			0: 45,
			1: 0,
			2: -45,
		},
        "position": 0,
        "lights" : {     
            "green" : True,
            "red" : False,
        },
        "flag" : "green",
        "momentary" : False,
    },
}

values = {
    "test_gauge": 0.1
}

indicators = {
    "lamp_test": True
}

buttons = {
    "test_button": False
}

recorders = {}

test_value = 0

def model_run(delta):
    global test_value
    if alarms == {}:
        return
    if buttons["test_button"]:
        test_value += 0.1
    values["test_gauge"] = math.sin(test_value) / 2 + 0.5
    indicators["lamp_test"] = switches["test_switch"]["position"] != 1
    alarms["test_alarm"]["state"] = AnnunciatorStates.CLEAR
    if switches["test_switch"]["position"] == 0:
        alarms["test_alarm"]["state"] = AnnunciatorStates.ACTIVE
    elif switches["test_switch"]["position"] == 2:
        alarms["test_alarm"]["state"] = AnnunciatorStates.ACTIVE_CLEAR

def model_run_fast(delta):
    pass
