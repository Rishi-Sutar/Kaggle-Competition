"""
Benchmark Agents.
Runs full 720-step games to compare our current agent (Phase 4) against the Phase 3 baseline.
"""
import sys, os
sys.path.insert(0, os.getcwd())
from kaggle_environments import make

def run_single_game(agent_path="main.py", opponent_path="phase3_agent/main.py", steps=720, seed=42):
    env = make("kaggriculture", configuration={"episodeSteps": steps, "seed": seed}, debug=False)
    env.run([agent_path, opponent_path])
    
    final_step = env.steps[-1]
    my_reward = final_step[0].reward
    opp_reward = final_step[1].reward
    won = my_reward > opp_reward
    tied = my_reward == opp_reward
    return my_reward, opp_reward, won, tied

def benchmark(num_games=5, agent_path="main.py", opponent_path="phase3_agent/main.py"):
    print(f"--- Running Benchmark: Current Agent vs {opponent_path} ({num_games} games, 720 steps each) ---")
    wins = 0
    ties = 0
    my_scores = []
    opp_scores = []
    
    for i in range(num_games):
        seed = 200 + i  # New seeds for fairness
        my_r, opp_r, won, tied = run_single_game(agent_path=agent_path, opponent_path=opponent_path, steps=720, seed=seed)
        my_scores.append(my_r)
        opp_scores.append(opp_r)
        if won:
            wins += 1
        elif tied:
            ties += 1
        print(f"Game {i+1:2d} (seed {seed}): My Money=${my_r:.1f}, Opponent=${opp_r:.1f} | {'WIN' if won else ('TIE' if tied else 'LOSS')}")
        
    avg_my = sum(my_scores) / len(my_scores)
    avg_opp = sum(opp_scores) / len(opp_scores)
    win_pct = (wins / num_games) * 100
    print(f"\nSummary vs Phase 3 Baseline:")
    print(f"  Win Rate: {wins}/{num_games} ({win_pct:.1f}%)")
    print(f"  Avg My Money: ${avg_my:.2f} (Net: ${avg_my - 3000:+.2f})")
    print(f"  Avg Opponent Money: ${avg_opp:.2f} (Net: ${avg_opp - 3000:+.2f})")
    
if __name__ == "__main__":
    benchmark(num_games=3)
