"""
Benchmark Phase 3 Baseline Agent.
Runs full 720-step games vs 'random' and 'pass' opponents.
Computes win rate, final money, and net profit.
"""
import sys, os
sys.path.insert(0, os.getcwd())
from kaggle_environments import make
from main import agent

def run_single_game(opponent="random", steps=720, seed=42):
    env = make("kaggriculture", configuration={"episodeSteps": steps, "seed": seed}, debug=False)
    env.run([agent, opponent])
    
    final_step = env.steps[-1]
    my_reward = final_step[0].reward
    opp_reward = final_step[1].reward
    won = my_reward > opp_reward
    tied = my_reward == opp_reward
    return my_reward, opp_reward, won, tied

def benchmark(num_games=5, opponent="random"):
    print(f"--- Running Benchmark vs {opponent} ({num_games} games, 720 steps each) ---")
    wins = 0
    ties = 0
    my_scores = []
    opp_scores = []
    
    for i in range(num_games):
        seed = 100 + i
        my_r, opp_r, won, tied = run_single_game(opponent=opponent, steps=720, seed=seed)
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
    print(f"\nSummary vs {opponent}:")
    print(f"  Win Rate: {wins}/{num_games} ({win_pct:.1f}%)")
    print(f"  Avg My Money: ${avg_my:.2f} (Net: ${avg_my - 3000:+.2f})")
    print(f"  Avg Opponent Money: ${avg_opp:.2f}")
    return win_pct, avg_my

if __name__ == "__main__":
    # Test 1 game vs pass first to check baseline farming mechanics
    print("Testing 1 full 720-step game vs 'pass'...")
    r0, r1, w, t = run_single_game(opponent="pass", steps=720, seed=42)
    print(f"Result vs pass: My=${r0:.1f}, Opp=${r1:.1f}")
    
    # Run 5 games vs random
    benchmark(num_games=5, opponent="random")
