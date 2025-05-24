import os
import mlflow
from stable_baselines3 import PPO
from simulation_engine.rl_env import SimulationEnv


def train(
    total_timesteps: int = 100_000,
    episode_length: int = 5,
    log_dir: str = "rl_runs",
    mlflow_experiment: str = "Simulation_Robustness_RL",
):
    # Ensure log directory exists
    os.makedirs(log_dir, exist_ok=True)
    mlflow.set_experiment(mlflow_experiment)
    with mlflow.start_run():
        # Log training parameters
        mlflow.log_param("total_timesteps", total_timesteps)
        mlflow.log_param("episode_length", episode_length)

        # Initialize RL environment
        env = SimulationEnv(turns_per_episode=episode_length)

        # Initialize PPO agent
        model = PPO("MlpPolicy", env, verbose=1)

        # Train the agent
        model.learn(total_timesteps=total_timesteps)

        # Save trained model
        model_path = os.path.join(log_dir, "ppo_simulation_agent")
        model.save(model_path)
        mlflow.log_artifact(
            model_path + ".zip" if os.path.exists(model_path + ".zip") else model_path
        )

        # Evaluate trained agent for one episode
        obs = env.reset()
        total_reward = 0.0
        done = False
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, done, info = env.step(action)
            total_reward += reward

        # Log evaluation metrics
        mlflow.log_metric("eval_reward", total_reward)
        print(f"Evaluation reward: {total_reward:.3f}")


if __name__ == "__main__":
    train()
