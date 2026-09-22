from kaggle_environments import make
import main

def test():
    env = make('kaggriculture', configuration={'episodeSteps': 75}, debug=True)
    env.run([main.agent, 'pass'])
    print('Completed 75 steps!')
    for s in [0, 1, 23, 24, 25, 47, 48, 49, 72, 73, 74]:
        step_obs = env.steps[s][0]['observation']
        my_farm = step_obs['farms'][0]
        priv = step_obs['private']
        animals_placed = sum(1 for y in range(5) for x in range(5) if my_farm['tiles'][y][x] and my_farm['tiles'][y][x].get('kind') in ('PASTURE', 'COOP') and my_farm['tiles'][y][x].get('animal'))
        fed_count = sum(1 for y in range(5) for x in range(5) if my_farm['tiles'][y][x] and my_farm['tiles'][y][x].get('kind') in ('PASTURE', 'COOP') and my_farm['tiles'][y][x].get('fed_today'))
        cared_count = sum(1 for y in range(5) for x in range(5) if my_farm['tiles'][y][x] and my_farm['tiles'][y][x].get('kind') in ('PASTURE', 'COOP') and my_farm['tiles'][y][x].get('cared_today'))
        plants = sum(1 for y in range(5) for x in range(5) if my_farm['tiles'][y][x] and my_farm['tiles'][y][x].get('kind') == 'PLANT')
        print(f"Step {s:2d} (Day {step_obs['day']} h{step_obs['hour']:2d}): money={my_farm['money']:6.1f} hands={len(my_farm['hands'])} animals={animals_placed} fed={fed_count} cared={cared_count} plants={plants} shed_wheat={priv['shed']['WHEAT']}")

if __name__ == '__main__':
    test()
