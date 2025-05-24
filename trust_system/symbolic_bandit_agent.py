import random


class SymbolicBanditAgent:
    def __init__(self, actions):
        self.actions = actions
        self.counts = {a: 0 for a in actions}
        self.values = {a: 0.0 for a in actions}

    def select_action(self):
        # Epsilon-greedy
        if random.random() < 0.1:
            return random.choice(self.actions)
        return max(self.actions, key=lambda a: self.values[a])

    def update(self, action, reward):
        self.counts[action] += 1
        n = self.counts[action]
        value = self.values[action]
        self.values[action] = value + (reward - value) / n
