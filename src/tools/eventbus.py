"""
Cyber Range integration module.

To allow any Red Team module to publish events to the Cyber Range,
this module defines an Event Bus where messages can be published.

This is an abstract interface that decouples Red Team modules from the 
specifics of the Cyber Range interface.
The Cyber Range has not yet defined an interface to interact with the Red Team,
therefore for now this module simply prints messages on screen.
"""

import json

from pydispatch import dispatcher


def handle_event(sender, event):
    """Simple event handler"""
    print(f'GAME EVENT ({sender}): {json.dumps(event, sort_keys=True, default=str)}')

dispatcher.connect(handle_event, signal='redteam-flags', sender=dispatcher.Any)
