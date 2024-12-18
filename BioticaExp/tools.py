# tools.py

feed = {
    "type": "function",
    "function": {
            "name": "feed",
            "description": "Lowers the mouse water bottle for a specified duration. Return true if the water bottle was lowered successfully, false otherwise.",
            "strict": True,
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
                "additionalProperties": False
            }
    }
}

play_sound = {
    "type": "function",
    "function": {
        "name": "play_sound",
        "description": "Plays sound in speaker in the mouse cage for a specified duration and frequency. The frequency range is 50 - 10000 Hz. Return true if the sound was played successfully, false otherwise.",
        "strict": True,
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
            "additionalProperties": False
        }
    }
}

wait_for_lever = {
    "type": "function",
    "function": {
        "name": "wait_for_lever",
        "description": "Wait for a specified duration until either lever is pressed by the mouse. There are two levers in the cage. Return 0 if the left lever is pressed, 1 if the right lever is pressed, and -1 if neither lever is pressed within the duration. You can wait for up to 2 minutes from a single call but you can call this function multiple times to wait for longer durations.",
        "strict": True,
        "parameters": {
            "type": "object",
            "required": [
                "duration"
            ],
            "properties": {
                "duration": {
                    "type": "number",
                    "description": "The time in seconds to wait for either lever to be pressed by the mouse. You can wait for up to 2 minutes from a single call but you can call this function multiple times to wait for longer durations."
                }
            },
            "additionalProperties": False
        }
    }
}

delay = {
    "type": "function",
    "function": {
        "name": "delay",
        "description": "Blocking function that makes the program wait for a specified duration. This function is useful because the experiment may last multiple hours or days and you may want to space out parts of your experiment. The maximum duration is 5 minutes, but feel free to repeatedly call this function to delay execution for longer durations.",
        "strict": True,
        "parameters": {
            "type": "object",
            "required": [
                "duration"
            ],
            "properties": {
                "duration": {
                    "type": "number",
                    "description": "The amount of time, in seconds, to delay execution. The maximum duration is 5 minutes."
                }
            },
            "additionalProperties": False
        }
    }
}

get_human_help = {
    "type": "function",
    "function": {
        "name": "get_human_help",
        "description": "When your are stuck, you can use this tool to get help/input from a human to adjust your experiment strategy. This tool can be used at most once every 1 hour and will be disabled if it was used within the last 1 hour (3600 seconds).",
        "strict": True,
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
            "additionalProperties": False
        }
    }
}

tools = [feed, play_sound, wait_for_lever, get_human_help]
