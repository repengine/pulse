"""
SimulationEnv: OpenAI Gym-style environment for RL-based rule adaptation in Pulse.
"""

import gymnasium as gym
import numpy as np
from rules.static_rules import build_static_rules
from rules.rule_param_registry import RULE_PARAM_REGISTRY


class SimulationEnv(gym.Env):
    def __init__(self, turns_per_episode=5):
        super().__init__()
        self.turns_per_episode = turns_per_episode
        self.current_turn = 0
        self.rule_ids = list(RULE_PARAM_REGISTRY.keys())
        self.param_names = [
            p for rid in self.rule_ids for p in RULE_PARAM_REGISTRY[rid]
        ]
        self.action_space = gym.spaces.Box(
            low=np.array(
                [
                    RULE_PARAM_REGISTRY[rid][p]["low"]
                    for rid in self.rule_ids
                    for p in RULE_PARAM_REGISTRY[rid]
                ]
            ),
            high=np.array(
                [
                    RULE_PARAM_REGISTRY[rid][p]["high"]
                    for rid in self.rule_ids
                    for p in RULE_PARAM_REGISTRY[rid]
                ]
            ),
            dtype=np.float32,
        )
        self.observation_space = gym.spaces.Box(
            low=-np.inf, high=np.inf, shape=(len(self.param_names),), dtype=np.float32
        )
        self.state = None
        self.reset()

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        self.current_turn = 0
        self.state = np.array(
            [
                RULE_PARAM_REGISTRY[rid][p]["default"]
                for rid in self.rule_ids
                for p in RULE_PARAM_REGISTRY[rid]
            ],
            dtype=np.float32,
        )
        info = {}
        return self.state.copy(), info

    def compute_robustness_reward(self, param_overrides):
        from engine.simulator_core import simulate_forward
        from engine.worldstate import WorldState

        state = WorldState()
        _rules = build_static_rules(param_overrides)
        results = simulate_forward(
            state,
            turns=self.turns_per_episode,
            use_symbolism=True,
            return_mode="summary",
        )
        last = results[-1] if results else {}
        fragility = last.get("fragility", 1.0)
        confidence = last.get("confidence", 0.0)
        drift = last.get("drift", 0.0)
        reward = confidence - fragility - drift
        return reward

    def step(self, action):
        action = np.clip(action, self.action_space.low, self.action_space.high)
        self.state = action.copy()
        param_overrides = {}
        idx = 0
        for rid in self.rule_ids:
            param_overrides[rid] = {}
            for p in RULE_PARAM_REGISTRY[rid]:
                param_overrides[rid][p] = float(action[idx])
                idx += 1
        reward = self.compute_robustness_reward(param_overrides)
        self.current_turn += 1
        terminated = self.current_turn >= self.turns_per_episode
        truncated = False
        info = {"param_overrides": param_overrides}
        return self.state.copy(), reward, terminated, truncated, info
