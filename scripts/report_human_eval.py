import argparse
import json
import os
from datetime import datetime


def compute_time_diff(begin_time, end_time):
    begin_time = datetime.fromisoformat(begin_time)
    end_time = datetime.fromisoformat(end_time)

    return (end_time - begin_time).total_seconds()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--result-dir", type=str, required=True)
    args = parser.parse_args()

    win_rate_over_autonomous = []
    agent_rating = []
    outcome_rating = []
    agent_message_cnt = []
    agent_task_action_cnt = []
    human_message_cnt = []
    human_task_action_cnt = []
    total_event = []
    session_time = []
    total_case = 0
    for d in os.listdir(args.result_dir):
        if "eval.json" not in d:
            continue
        env_id = d.split("_")[0]
        eval_result = json.load(open(os.path.join(args.result_dir, d)))
        if os.path.exists(
            os.path.join(args.result_dir, f"env_{env_id}", "event_log.json")
        ):
            event_log = json.load(
                open(os.path.join(args.result_dir, f"env_{env_id}", "event_log.json"))
            )
        elif os.path.exists(
            os.path.join(args.result_dir, f"env_{env_id}", "event_log.jsonl")
        ):
            event_log = []
            with open(
                os.path.join(args.result_dir, f"env_{env_id}", "event_log.jsonl")
            ) as f:
                for line in f:
                    event_log.append(json.loads(line))
        else:
            print(f"Event log not found for {env_id}")
            continue
        win_rate_over_autonomous.append(eval_result["outcome_preference"] == "Final")
        agent_rating.append(eval_result["agent_rating"])
        outcome_rating.append(eval_result["outcome_rating"])
        total_event.append(len(event_log))
        agent_message_cnt.append(0)
        agent_task_action_cnt.append(0)
        human_message_cnt.append(0)
        human_task_action_cnt.append(0)
        for event in event_log:
            if "agent" in event["role"]:
                if event["action_type"] == "environment":
                    agent_task_action_cnt[-1] += 1
                else:
                    agent_message_cnt[-1] += 1
            elif "user" in event["role"]:
                if event["action_type"] == "environment":
                    human_task_action_cnt[-1] += 1
                else:
                    human_message_cnt[-1] += 1

        begin_time = event_log[0]["timestamp"]
        end_time = event_log[-1]["timestamp"]
        session_time.append(compute_time_diff(begin_time, end_time) / 60)
        total_case += 1

    print(f"Total case: {total_case}")
    print(f"Win rate over autonomous: {sum(win_rate_over_autonomous) / total_case}")
    print(f"Agent rating: {sum(agent_rating) / total_case}")
    print(f"Outcome rating: {sum(outcome_rating) / total_case}")
    print(f"Agent message count: {sum(agent_message_cnt) / total_case}")
    print(f"Agent task action count: {sum(agent_task_action_cnt) / total_case}")
    print(f"Human message count: {sum(human_message_cnt) / total_case}")
    print(f"Human task action count: {sum(human_task_action_cnt) / total_case}")
    print(f"Total event: {sum(total_event) / total_case}")
    print(f"Session time: {sum(session_time) / total_case}")


if __name__ == "__main__":
    main()
