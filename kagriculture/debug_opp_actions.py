import json
with open('episode-111349513-replay.json') as f:
    replay = json.load(f)

team_names = replay['info'].get('TeamNames', ['Agent0', 'Agent1'])
my_idx = 0 if 'Rishi' in team_names[0] or 'Phase' in team_names[0] or 'submission' in team_names[0] or str(team_names[0]) == '1' else 1
opp_idx = 1 - my_idx

for i in range(25):
    step = replay['steps'][i]
    actions = step[opp_idx]['action']
    market_actions = actions.get('market', [])
    print(f'Step {i} market actions: {market_actions}')
    
    if i > 0:
        obs = step[0]['observation']
        opp_farm = obs['farms'][opp_idx]
        print(f"  Money: {opp_farm['money']}")
        print(f"  Farmer: {actions.get('farmer')}, Hands: {actions.get('hands')}")
