"""
Phase 0.6 — Discover the ACTUAL action format from the environment spec.
"""
import sys, os
sys.path.insert(0, os.getcwd())
from kaggle_environments import make
import json

env = make("kaggriculture", configuration={"episodeSteps": 24, "seed": 42}, debug=True)

# Print the environment specification
print("=" * 70)
print("ENVIRONMENT SPECIFICATION")
print("=" * 70)
spec = env.specification
print(json.dumps(spec, indent=2, default=str))

print("\n" + "=" * 70)
print("ENVIRONMENT CONFIGURATION")
print("=" * 70)
print(json.dumps(env.configuration, indent=2, default=str))

# Also check what actions the env expects
print("\n" + "=" * 70)
print("ACTION SPACE")
print("=" * 70)
if hasattr(env, 'action_space'):
    print(env.action_space)
else:
    print("No action_space attribute")

# Check environment source if possible
print("\n" + "=" * 70)
print("ENVIRONMENT HTML (action info)")
print("=" * 70)
if hasattr(env, 'html'):
    # The HTML sometimes contains JS with action definitions
    html = str(env.html) if env.html else ""
    if len(html) > 500:
        print(f"HTML length: {len(html)} chars (too long to print)")
    else:
        print(html)
