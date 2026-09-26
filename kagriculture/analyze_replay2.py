import json, os

replay_files = sorted([f for f in os.listdir('.') if f.endswith('-replay.json')])

for replay_file in replay_files:
    with open(replay_file) as f:
        replay = json.load(f)

    steps = replay.get('steps', [])
    final = steps[-1]

    money = []
    for i, agent_data in enumerate(final):
        obs = agent_data.get('observation', {})
        farms = obs.get('farms', [])
        if farms and i < len(farms):
            money.append(farms[i].get('money', 0))

    winner = 'P0 WINS' if money[0] > money[1] else ('P1 WINS' if money[1] > money[0] else 'TIE')
    print(f'\n{"="*60}')
    print(f'Replay: {replay_file}')
    print(f'P0: ${money[0]:,.0f}  |  P1: ${money[1]:,.0f}  -> {winner}')

    # Track all seeds/animals over entire game for each player
    all_seeds = {'P0': {}, 'P1': {}}
    all_animals = {'P0': {}, 'P1': {}}
    all_sells = {'P0': {}, 'P1': {}}
    hire_count = {'P0': 0, 'P1': 0}

    for step_idx, step in enumerate(steps):
        for player_idx, agent_data in enumerate(step):
            pk = f'P{player_idx}'
            action = agent_data.get('action', {})
            for order in action.get('market', []):
                if not order:
                    continue
                op = order[0]
                item = order[1] if len(order) > 1 else ''
                qty = order[2] if len(order) > 2 else 1
                if op == 'BUY_SEED':
                    all_seeds[pk][item] = all_seeds[pk].get(item, 0) + qty
                elif op == 'BUY_ANIMAL':
                    all_animals[pk][item] = all_animals[pk].get(item, 0) + qty
                elif op == 'SELL':
                    all_sells[pk][item] = all_sells[pk].get(item, 0) + qty
                elif op == 'HIRE':
                    hire_count[pk] += 1

    print(f'  P0 seeds: {all_seeds["P0"]}')
    print(f'  P1 seeds: {all_seeds["P1"]}')
    print(f'  P0 animals: {all_animals["P0"]}')
    print(f'  P1 animals: {all_animals["P1"]}')
    print(f'  P0 total sold: {all_sells["P0"]}')
    print(f'  P1 total sold: {all_sells["P1"]}')
    print(f'  P0 hires: {hire_count["P0"]}  |  P1 hires: {hire_count["P1"]}')
