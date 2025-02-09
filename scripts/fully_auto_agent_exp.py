"""
Experiment script for running fully autonomous agent experiments.
"""

import argparse
import atexit
import os
import signal
import sys
import time
import toml

from collaborative_gym.core import TeamMemberConfig
from collaborative_gym.runner import Runner
from collaborative_gym.utils.string import make_string_green


TABULAR_ANALYSIS_CONFIG_TEMPLATE = """env_class = "tabular_analysis"

[env_args]
use_simulated_dataset = true
discovery_bench_data_point_idx = {idx}"""

TRAVEL_PLANNING_CONFIG_TEMPLATE = """env_class = "travel_planning"

[env_args]
use_simulated_dataset = true
travel_planner_data_point_idx = {idx}"""

LIT_SURVEY_CONFIG_TEMPLATE = """env_class = "lit_survey"

[env_args]
use_simulated_dataset = true
simulated_data_point_idx = {idx}"""


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Run fully autonomous agent experiments."
    )
    parser.add_argument("--task", type=str, required=True,
                        choices=["related_work", "tabular_analysis", "travel_planning"],
                        help="The experiment task to run.")
    parser.add_argument("--work-dir", type=str, default="./workdir",
                        help="Working directory for the experiment.")
    parser.add_argument("--start-idx", type=int, required=True,
                        help="Start index for experiments.")
    parser.add_argument("--end-idx", type=int, required=True,
                        help="The end index (exclusive) for experiments.")
    parser.add_argument("--team-member-config-path", type=str,
                        default="configs/pure_agent_team_config.toml",
                        help="Path to the team member configuration file.")
    parser.add_argument("--result-dir-tag", type=str, required=True,
                        help="Tag used to identify the results directory.")
    parser.add_argument("--secret-path", type=str, default="secrets.toml",
                        help="Path to the secrets file.")
    parser.add_argument("--redis-url", type=str, default="redis://localhost:6379/0",
                        help="Redis URL for backend services.")
    return parser.parse_args()


def load_and_set_secrets(secret_path):
    secrets = toml.load(secret_path)
    for key, value in secrets.items():
        os.environ[key] = value


def create_env_config_dir(work_dir, task, result_dir_tag):
    env_config_dir = os.path.join(work_dir, f"{task}/{result_dir_tag}/env_config_tmp")
    os.makedirs(env_config_dir, exist_ok=True)
    return env_config_dir


def select_config_template(task):
    if task == "related_work":
        return LIT_SURVEY_CONFIG_TEMPLATE
    elif task == "tabular_analysis":
        return TABULAR_ANALYSIS_CONFIG_TEMPLATE
    elif task == "travel_planning":
        return TRAVEL_PLANNING_CONFIG_TEMPLATE
    else:
        raise ValueError(f"Unsupported task: {task}")


def init_runner(work_dir, task, result_dir_tag):
    results_path = os.path.join(work_dir, f"{task}/{result_dir_tag}/results")
    return Runner(result_dir=results_path)


def register_exit_signals(runner):
    def handle_exit_signal(signum, frame):
        runner.cleanup_subprocesses()
        sys.exit(0)

    atexit.register(runner.cleanup_subprocesses)
    signal.signal(signal.SIGINT, handle_exit_signal)
    signal.signal(signal.SIGTERM, handle_exit_signal)


def run_experiments(args, env_config_dir, config_template, runner, team_member_config):
    for idx in range(args.start_idx, args.end_idx):
        runner.reset()
        start_time = time.time()
        print(make_string_green(f"Starting experiment for {args.task} with index {idx}"))
        
        config_path = os.path.join(env_config_dir, f"{args.task}_{idx}.toml")
        with open(config_path, "w") as f:
            f.write(config_template.format(idx=idx))
        
        runner.start_session(
            session_uuid=f"{args.task}_{idx}",
            env_config_path=config_path,
            members=[TeamMemberConfig(**member) for member in team_member_config["team_member"]],
            max_steps=30,
            disable_collaboration=True,
            add_tick=False,
        )
        
        for node_process in runner.subprocesses:
            node_process.wait()
        
        time_spent = (time.time() - start_time) / 60
        print(make_string_green(
            f"Experiment for {args.task} with index {idx} completed in {time_spent:.2f} minutes."
        ))


def main():
    args = parse_arguments()
    load_and_set_secrets(args.secret_path)
    
    env_config_dir = create_env_config_dir(args.work_dir, args.task, args.result_dir_tag)
    config_template = select_config_template(args.task)
    runner = init_runner(args.work_dir, args.task, args.result_dir_tag)
    register_exit_signals(runner)
    
    team_member_config = toml.load(args.team_member_config_path)
    run_experiments(args, env_config_dir, config_template, runner, team_member_config)


if __name__ == "__main__":
    main()
