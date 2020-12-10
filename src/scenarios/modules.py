import yaml
import os

from src.campaigns.models import Campaign, Logic, AdversaryTree
from src.adversaries.models import Adversary
from src.tools.settings import ADVERSARY, CAMPAIGN, BASE_DIR


class Planner:
    def __init__(self, campaign_plan=CAMPAIGN, adversary_profile=ADVERSARY, auto=True):

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
        path = os.path.join(BASE_DIR, 'campaigns', 'plans', plan)

        with open(path, 'r') as data:
            data_loaded = yaml.safe_load(data)
            self._campaign = Campaign(plan=data_loaded)

    @property
    def adversary(self):
        return self._adversary

    @adversary.setter
    def adversary(self, plan):
        plan = f'{plan}.yml'
        path = os.path.join(BASE_DIR, 'adversaries', 'profiles', plan)

        with open(path, 'r') as data:
            data_loaded = yaml.safe_load(data)
            self._adversary = Adversary(profile=data_loaded)

    @staticmethod
    def run(tree, logic, preconditions, flags):
        logic(tree, flags, preconditions)
