%%writefile main.py
printed = False

def probe_agent(obs):
    global printed

    if not printed:
        print("=" * 80)
        print("INITIAL OBSERVATION")
        print("=" * 80)

        from pprint import pprint
        pprint(obs)

        printed = True

    return {
        "farmer": ["PASS"],
        "market": [],
    }
