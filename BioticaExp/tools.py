# tools.py

feed = {
    "type": "function",
    "function": {
            "name": "feed",
            "description": "Lowers the mouse water bottle for a specified duration. Return true if the water bottle was lowered successfully, false otherwise.",
            "strict": true,
            "parameters": {
                "type": "object",
                "required": [
                    "duration"
                ],
                "properties": {
                    "duration": {
                        "type": "number",
                        "description": "The duration to lower the mouse water bottle in seconds"
                    }
                },
                "additionalProperties": false
            }
    }
}

play_sound = {
    "name": "play_sound",
    "description": "Plays sound in speaker in the mouse cage for a specified duration and frequency. The frequency range is 50 - 10000 Hz. Return true if the sound was played successfully, false otherwise.",
    "strict": true,
    "parameters": {
        "type": "object",
        "required": [
            "duration",
            "frequency"
        ],
        "properties": {
            "duration": {
                "type": "number",
                "description": "The duration of the sound in seconds."
            },
            "frequency": {
                "type": "number",
                "description": "The frequency of the sound in Hertz. The frequency range is 50 - 10000 Hz. Do not play sound outside this range because it will damage the speaker!"
            }
        },
        "additionalProperties": false
    }
}

wait_for_lever = {
    "name": "wait_for_lever",
    "description": "Wait for a specified duration until either lever is pressed by the mouse. There are two levers in the cage. Return 0 if the left lever is pressed, 1 if the right lever is pressed, and -1 if neither lever is pressed within the timeout.",
    "strict": true,
    "parameters": {
        "type": "object",
        "required": [
            "timeout"
        ],
        "properties": {
            "timeout": {
                "type": "number",
                "description": "The time in seconds to wait for either lever to be pressed by the mouse."
            }
        },
        "additionalProperties": false
    }
}

delay = {
    "name": "delay",
    "description": "Blocking function that makes the program wait for a specified duration. This function is useful because the experiment may last multiple hours or days and you may want to space out parts of your experiment.",
    "strict": true,
    "parameters": {
        "type": "object",
        "required": [
            "duration"
        ],
        "properties": {
            "duration": {
                "type": "number",
                "description": "The amount of time, in seconds, to delay execution"
            }
        },
        "additionalProperties": false
    }
}

get_human_help = {
    "name": "get_human_help",
    "description": "When your are stuck, you can use this tool to get help/input from a human to adjust your experiment strategy. This tool can be used at most once every 24 hours and will be disabled if it was used within the last 24 hours.",
    "strict": true,
    "parameters": {
        "type": "object",
        "required": [
            "request"
        ],
        "properties": {
            "request": {
                "type": "string",
                "description": "The request message explaining the strategy you are using and what help you want from the human."
            }
        },
        "additionalProperties": false
    }
}

tools = [feed, play_sound, wait_for_lever, delay, get_human_help]