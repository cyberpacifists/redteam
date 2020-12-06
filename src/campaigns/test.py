if __name__ == '__main__':
    from src.campaigns.models import Campaign
    from src.tools.models import Schema

    a = Schema('all')
    c = Campaign(schema=a, flags={'reconnaissance': 'a'})
    c.build()

    art = c.get_tree()[0]
    art.run_technique("Conduct active scanning")
    tec = art.get_technique("Conduct active scanning")

    print(tec.is_burnt())
