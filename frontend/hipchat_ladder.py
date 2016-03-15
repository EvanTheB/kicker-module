"""
willie IRC frontend for wrank.
Load this file in the willie modules directory.
"""

import sys
import os
import wrank.front

import requests



ladder = wrank.front.LadderManager("kicker.log")

htmels = "<pre>" + "<br>".join(ladder.ladder_command(["ladder", "ELO"])) + "</pre>"

print requests.post(os.environ["LADDER_HIPCHAT_OATH"], data={
    "color": "green",
    "message": htmels,
    "notify": False,
    "message_format": "html"
}
)
