import sys, os
from kaggle_environments import make

def market_spy_agent(obs, conf):
    step = obs["step"]
    if step < 5:
        market = obs["market"]
        inv = market.get("inventory", {})
        prices = market.get("prices", {})
        print(f"Step {step}: WHEAT: Price={prices.get('WHEAT', 0)}, Inventory={inv.get('WHEAT', 0)}")
    
    if step == 0:
        return {"farmer": ["PASS"], "hands": [], "market": [["BUY_PRODUCT", "WHEAT", 50]]}
    elif step == 1:
        return {"farmer": ["PASS"], "hands": [], "market": [["SELL", "WHEAT", 50]]}
    return {"farmer": ["PASS"], "hands": [], "market": []}

env = make("kaggriculture", configuration={"episodeSteps": 10, "seed": 42}, debug=True)
env.run([market_spy_agent, "pass"])
