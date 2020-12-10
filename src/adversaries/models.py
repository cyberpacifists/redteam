"""
These adversaries are meant to add another level of interaction with the blue team.

Generally, adversaries can be classified by their motive and the way they do things.
To be more precise, adversaries use different schemas and techniques depending on their purpose.

Let's say, a hack-activist will follow different paths and use different methods to a burglar, and that one from
a government employee.

These classes will define how they interact with the systems, how destructive they are, how intrusive, which tools
they will use, and so on.
"""
from src.tools.models import Schema
from src.campaigns.models import Campaign


class Adversary:
    """
    This class is the top level adversary, the decisions maker, the way the app behaves
    """
    __campaign: Campaign = None

    def __init__(self, profile):
        self.profile = profile

    @property
    def profile(self):
        return self._profile

    @profile.setter
    def profile(self, profile_object: object):
        profile = profile_object
        self._profile = profile

        self.logic = profile["logic"]
        self.schema = Schema(profile["schema"])
