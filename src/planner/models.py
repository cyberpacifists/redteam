import yaml
import os

# the package manager from python is retarded. This packages exist, are local, no worries about the retarded errors
from tools.models import AdversaryTree, ArtifactNode, Schema, Logic
from tools.settings import ADVERSARY, CAMPAIGN, BASE_DIR


def main(auto=True):
    Planner(auto=auto)


class Planner:
    def __init__(self, campaign_plan: str = CAMPAIGN, adversary_profile: str = ADVERSARY, auto=True):
        # build the campaign and the adversary
        self.campaign = campaign_plan
        self.adversary = adversary_profile

        self.tree = AdversaryTree(
            self.campaign.schema,
            self.adversary.schema
        ).get_tree()

        self.logic = getattr(Logic, self.adversary.logic)

        if auto:
            self.run(self.tree, self.logic, self.campaign.preconditions, self.campaign.flags)

    @property
    def campaign(self):
        return self._campaign

    @campaign.setter
    def campaign(self, plan):
        plan = f'{plan}.yml'
        path = os.path.join(BASE_DIR, 'tools', 'campaigns', plan)

        with open(path, 'r') as data:
            data_loaded = yaml.safe_load(data)
            self._campaign = Campaign(plan=data_loaded)

    @property
    def adversary(self):
        return self._adversary

    @adversary.setter
    def adversary(self, plan):
        plan = f'{plan}.yml'
        path = os.path.join(BASE_DIR, 'tools', 'adversaries', plan)

        with open(path, 'r') as data:
            data_loaded = yaml.safe_load(data)
            self._adversary = Adversary(profile=data_loaded)

    @staticmethod
    def run(tree, logic, preconditions, flags):
        logic(tree, flags, preconditions)


class Campaign:
    """
    Campaigns are just meant to declare an abstract structure of how and which TTP categories will be used for a
    specific scenario.
    That is, a campaign is meant to set up the scenario and the limitations.
    """

    def __init__(self, plan):
        self.plan_ = plan

    @property
    def plan_(self):
        return self._plan

    @plan_.setter
    def plan_(self, plan):
        self._plan = plan
        self.preconditions = plan["preconditions"] if "preconditions" in plan else None
        self.schema = Schema(plan["schema"])
        self.flags = self.schema.flags


class Adversary:
    """
    This class is the top level adversary, the decisions maker, the way the app behaves
    """

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
