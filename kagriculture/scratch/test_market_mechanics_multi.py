import sys, os
from kaggle_environments import make

def market_spy_agent(obs, conf):
    step = obs["step"]
    if step < 50:
        market = obs["market"]
        inv = market.get("inventory", {})
        prices = market.get("prices", {})
        
        print(f"Step {step}:")
        for item in ["WHEAT", "MILK", "WOOL", "BEEF"]:
            if item in inv:
                print(f"  {item}: Price={prices.get(item, 0)}, Inventory={inv.get(item, 0)}")
    return "pass"

env = make("kaggriculture", configuration={"episodeSteps": 100, "seed": 42}, debug=True)
env.run([market_spy_agent, "pass"])
