import sys, os
from kaggle_environments import make

# Add the parent directory to sys.path so we can import from the main module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import agent

if __name__ == "__main__":
    env = make("kaggriculture", configuration={"episodeSteps": 100, "seed": 42}, debug=True)
    env.run([agent, "pass"])
    print("Environment ran successfully with main agent!")
