import sys, os
from kaggle_environments import make

def market_spy_agent(obs, conf):
    step = obs["step"]
    if step < 50:
        market = obs["market"]
        inv = market.get("inventory", {})
        prices = market.get("prices", {})
        
        # Print wheat specifically to observe
        if "WHEAT" in inv:
            print(f"Step {step} WHEAT: Price={prices.get('WHEAT', 0)}, Inventory={inv.get('WHEAT', 0)}")
    return "pass"

env = make("kaggriculture", configuration={"episodeSteps": 50, "seed": 42}, debug=True)
env.run([market_spy_agent, "pass"])
