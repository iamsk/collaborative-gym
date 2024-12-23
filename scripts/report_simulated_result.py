import argparse
import json
import os


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--result-dir", type=str, required=True)
    args = parser.parse_args()

    total_cnt = 0
    complete = []
    completed_task_performance = []
    collaboration_score = []
    action_cnt = {"agent": [], "user": []}
    message_cnt = {"agent": [], "user": []}
    for d in os.listdir(args.result_dir):
        if os.path.isdir(os.path.join(args.result_dir, d)):
            task_performance = json.load(
                open(os.path.join(args.result_dir, d, "task_performance.json"))
            )
            if len(task_performance["outcome"].strip()) == 0:
                # task not completed if outcome is empty
                task_performance["task_completion"] = 0
                task_performance["performance_rating"] = 0
                with open(
                    os.path.join(args.result_dir, d, "task_performance.json"), "w"
                ) as f:
                    json.dump(task_performance, f, indent=4)
            total_cnt += 1
            complete.append(task_performance["task_completion"])
            if task_performance["task_completion"] == 1:
                completed_task_performance.append(
                    task_performance["performance_rating"]
                )
            if type(task_performance["performance_rating"]) == str:
                print(f"Performance rating not found for {d}")
            collaboration_score.append(
                task_performance["task_completion"]
                * task_performance["performance_rating"]
            )
            event_log = []
            with open(os.path.join(args.result_dir, d, "event_log.jsonl")) as f:
                for line in f:
                    event_log.append(json.loads(line))
            agent_action_cnt = 0
            user_action_cnt = 0
            agent_collaborative_action_cnt = 0
            user_collaborative_action_cnt = 0
            for e in event_log:
                if "agent" in e["role"]:
                    agent_action_cnt += 1
                    if e["action_type"] == "collaborative":
                        agent_collaborative_action_cnt += 1
                elif "user" in e["role"]:
                    user_action_cnt += 1
                    if e["action_type"] == "collaborative":
                        user_collaborative_action_cnt += 1
            action_cnt["agent"].append(agent_action_cnt)
            action_cnt["user"].append(user_action_cnt)
            message_cnt["agent"].append(agent_collaborative_action_cnt)
            message_cnt["user"].append(user_collaborative_action_cnt)

    aggregated_result = {
        "delivery_rate": sum(complete) / total_cnt,
        "task_performance": sum(completed_task_performance)
        / len(completed_task_performance),
        "collaboration_score": sum(collaboration_score) / total_cnt,
        "average_agent_action_cnt": sum(action_cnt["agent"]) / total_cnt,
        "avg_user_action_cnt": sum(action_cnt["user"]) / total_cnt,
        "avg_agent_message_cnt": sum(message_cnt["agent"]) / total_cnt,
        "avg_user_message_cnt": sum(message_cnt["user"]) / total_cnt,
    }

    json.dump(
        aggregated_result,
        open(os.path.join(args.result_dir, "aggregated_result.json"), "w"),
        indent=4,
    )


if __name__ == "__main__":
    main()
