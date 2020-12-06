from src.adversaries.models import Adversary
from src.campaigns.models import Campaign
from src.tools.models import Schema
import yaml

if __name__ == '__main__':
    profile = yaml.safe_load(open("./profiles/hacker.yaml"))
    adversary = Adversary(profile)
    schema = Schema('all')
    campaign = Campaign(schema=schema, flags={'reconnaissance': 'a'})

    tree, logic = adversary.build_adversary(campaign)

    logic(tree)
