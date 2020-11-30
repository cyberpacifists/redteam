# -*- coding: utf-8 -*-
"""
Cyber Range game integration module
"""

import json

from pydispatch import dispatcher


def handle_event(sender, msg, obj):
    """Simple event handler"""
    print(f'GAME EVENT ({sender}): {msg}\n{json.dumps(obj, indent=2, sort_keys=True, default=str)}')

dispatcher.connect(handle_event, signal='operations', sender=dispatcher.Any)
