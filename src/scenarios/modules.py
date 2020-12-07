import yaml
import os

from src.campaigns.models import Campaign
from src.adversaries.models import Adversary
from src.tools.settings import ADVERSARY, CAMPAIGN, NETWORKS,BASE_DIR


class Planner:
    def __init__(self, campaign_plan=CAMPAIGN, adversary_profile=ADVERSARY):

        # build the campaign and the adversary
        self.campaign = campaign_plan
        self.adversary = adversary_profile

        self.tree, self.logic = self.adversary.build_adversary(self.campaign)

    @property
    def campaign(self):
        return self._campaign

    @campaign.setter
    def campaign(self, plan):
        plan = f'{plan}.yml'
        path = os.path.join(BASE_DIR, 'campaigns', 'plans', plan)

        with open(path, 'r') as data:
            data_loaded = yaml.safe_load(data)
            self._campaign = Campaign(techniques=data_loaded['techniques'], flags=data_loaded['flags'])

    @property
    def adversary(self):
        return self._adversary

    @adversary.setter
    def adversary(self, plan):
        plan = f'{plan}.yml'
        path = os.path.join(BASE_DIR, 'adversaries', 'profiles', plan)

        with open(path, 'r') as data:
            data_loaded = yaml.safe_load(data)
            self._adversary = Adversary(profile=data_loaded, networks=NETWORKS)



