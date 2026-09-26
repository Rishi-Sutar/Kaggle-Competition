import json, os

replay_files = [f for f in os.listdir('.') if f.endswith('-replay.json')]
print('Replay files:', replay_files)

target = sorted(replay_files, key=lambda f: os.path.getsize(f), reverse=True)[0]
print(f'Analyzing: {target} ({os.path.getsize(target)//1024}KB)')

with open(target) as f:
    replay = json.load(f)

steps = replay.get('steps', [])
print(f'Total steps: {len(steps)}')

# Check final state
final = steps[-1]
for i, agent_data in enumerate(final):
    obs = agent_data.get('observation', {})
    farms = obs.get('farms', [])
    if farms:
        farm = farms[i] if i < len(farms) else {}
        money = farm.get('money', '?')
        print(f'Player {i} final money: {money}')

# Analyze Day 0 actions (first 48 steps) for both players
print('\n=== Day 0-1 Actions ===')
for step_idx in range(min(48, len(steps))):
    step = steps[step_idx]
    for player_idx, agent_data in enumerate(step):
        action = agent_data.get('action', {})
        market = action.get('market', [])
        farmer = action.get('farmer', [])
        if market or (farmer and farmer != ['PASS']):
            print(f'  Step {step_idx} P{player_idx}: farmer={farmer}, market={market}')

# Check what crops/animals are bought by day 5
print('\n=== Market purchase summary Days 0-5 ===')
buys = {'BUY_SEED': {}, 'BUY_ANIMAL': {}}
for step_idx in range(min(120, len(steps))):
    step = steps[step_idx]
    for player_idx, agent_data in enumerate(step):
        action = agent_data.get('action', {})
        for order in action.get('market', []):
            if order and order[0] in buys:
                key = f'P{player_idx}_{order[1]}' if len(order) > 1 else f'P{player_idx}'
                buys[order[0]][key] = buys[order[0]].get(key, 0) + (order[2] if len(order) > 2 else 1)

print('Seeds bought:', buys['BUY_SEED'])
print('Animals bought:', buys['BUY_ANIMAL'])
