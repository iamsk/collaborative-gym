"""Experiment script for running fully autonomous agent experiments."""

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
    data_point_idx = {idx}"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--task",
        type=str,
        required=True,
        choices=["related_work", "tabular_analysis", "travel_planning"],
    )
    parser.add_argument("--work-dir", type=str, default="./workdir")
    parser.add_argument("--start-idx", type=int, required=True)
    parser.add_argument(
        "--end-idx", type=int, required=True, help="The end index is exclusive."
    )
    parser.add_argument(
        "--team-member-config-path",
        type=str,
        default="configs/pure_agent_team_config.toml",
    )
    parser.add_argument("--result-dir-tag", type=str, required=True)
    parser.add_argument("--secret-path", type=str, default="secrets.toml")
    parser.add_argument("--redis-url", type=str, default="redis://localhost:6379/0")
    args = parser.parse_args()

    secrets = toml.load(args.secret_path)
    for k in secrets:
        os.environ[k] = secrets[k]

    env_config_tmp_dir = os.path.join(
        args.work_dir, f"{args.task}/{args.result_dir_tag}/env_config_tmp"
    )
    if not os.path.exists(env_config_tmp_dir):
        os.makedirs(env_config_tmp_dir)

    if args.task == "related_work":
        config_template = LIT_SURVEY_CONFIG_TEMPLATE
    elif args.task == "tabular_analysis":
        config_template = TABULAR_ANALYSIS_CONFIG_TEMPLATE
    elif args.task == "travel_planning":
        config_template = TRAVEL_PLANNING_CONFIG_TEMPLATE

    # Initialize the Co-Gym runner.
    runner = Runner(
        result_dir=os.path.join(
            args.work_dir, f"{args.task}/{args.result_dir_tag}/results"
        )
    )

    def handle_exit_signal(signum, frame):
        runner.cleanup_subprocesses()
        sys.exit(0)

    atexit.register(runner.cleanup_subprocesses)
    signal.signal(signal.SIGINT, handle_exit_signal)
    signal.signal(signal.SIGTERM, handle_exit_signal)

    team_member_config = toml.load(args.team_member_config_path)

    for idx in range(args.start_idx, args.end_idx):
        runner.reset()
        start_time = time.time()
        print(
            make_string_green(f"Starting experiment for {args.task} with index {idx}")
        )
        with open(
            os.path.join(env_config_tmp_dir, f"{args.task}_{idx}.toml"), "w"
        ) as f:
            f.write(config_template.format(idx=idx))

        runner.start_session(
            session_uuid=f"{args.task}_{idx}",
            env_config_path=os.path.join(env_config_tmp_dir, f"{args.task}_{idx}.toml"),
            members=[
                TeamMemberConfig(**member)
                for member in team_member_config["team_member"]
            ],
            max_steps=30,
            disable_collaboration=True,
            add_tick=False,
        )

        for node_process in runner.subprocesses:
            node_process.wait()

        time_spent = (time.time() - start_time) / 60
        print(
            make_string_green(
                f"Experiment for {args.task} with index {idx} completed in {time_spent:.2f} minutes."
            )
        )


if __name__ == "__main__":
    main()
