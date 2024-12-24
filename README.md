<p align="center">
  <img src="assets/logo.svg" style="width: 60%; height: auto;">
</p>

---

<p align="center">
  <img src="assets/teaser-image-github.png" style="width: 100%; height: auto;">
</p>

## What is Collaborative Gym (Co-Gym)?
Collaborative Gym (Co-Gym) is a framework for enabling and evaluating **Human-Agent Collaboration**. It is designed to facilitate the development of collaborative agents that can act as teammates rather than mere tools. Specifically, Co-Gym provides API to support asynchronous tripartite interaction between agents, humans, and task environments, as well as a series of metrics to evaluate the human-agent collaboration outcome and processes.

## Setup
**We view Co-Gym as a framework for building and evaluating collaborative agents that take initiative at the correct time and work together with humans in parallel. We are working on enhancing our codebase to increase its extensibility. Stay tuned!**

Below, we provide a quick start guide to run Co-Gym locally to reproduce our experiments.

1. Install the required packages:
   ```shell
   conda create -n cogym python=3.11
   conda activate cogym
   pip install -r requirements.txt
   ```
2. Set up API keys: Copy `secrets.example.toml` from the root directory and rename it to `secrets.toml`. Complete the required fields by following the instructions provided in the comment.
3. To use the Jupyter Executor in task environment, create the docker image for execution:
    ```shell
    cd docker
    docker build -f Dockerfile_cpu -t cogym-jupyter-cpu-image .
    ```

## API
The Co-Gym API models environment where humans and agents can work together as Python [`CoEnv`](collaborative_gym/core.py) classes. We currently support three task environments:
- `CoTravelPlanningEnv(CoEnv)`: Collaborative environment for planning travel itineraries, supporting several search functionalities, distance matrix, and editing travel plans.
- `CoLitSurveyEnv(CoEnv)`: Collaborative environment for conducting literature survey (e.g., writing Related Work section for research), supporting searching for papers, taking notes, and writing/polishing a related works section.
- `CoAnalysisEnv(CoEnv)`: Collaborative environment for analyzing tabular data in csv format, supporting executing code in Jupyter notebook and documenting findings.

Creating environment instances and interacting with them is simple - here's an example using `CoTravelPlanningEnv`:
```python
from collaborative_gym.envs import EnvFactory
env = EnvFactory.make(
  name="travel_planning",
  team_members=["agent", "human"],
  env_id="env_1234",
  use_simulated_dataset=False,
  query="Help me plan a 5-day trip to Vancouver in December for a single person."
)

# In asynchronous collaboration, at a certain timestamp,
# agent can choose to take a task action like the following
obs, reward, terminated, private, info = env.step(
  role="agent",
  action="EDITOR_UPDATE(text=\"This is a placeholder.\")"
)
```

To support asynchronous interaction between agents, humans, and task environments, we use [Redis](https://redis.io/) for cross-process communication, and wrap each environment class with [`TaskEnvNode`](collaborative_gym/nodes/task_env.py). See [`collaborative_gym/nodes`](collaborative_gym/nodes) for other supported nodes (i.e., agents, real humans, simulated humans).

We provide a [`Runner`](collaborative_gym/runner.py) class to handles the lifecycle of human-agent collaboration sessions, including launching these node processes and ensuring proper clearnup on exit.

## Supported Conditions
Co-Gym supports two experimental conditions: Co-Gym (Simulated) and Co-Gym (Real)
- Co-Gym (Simulated) experiments with simulated humans and pre-collected task instances, allowing controlled, interative development.
- Co-Gym (Real) experiments with real humans and user provided task instances, allowing deploying and evaluating collaborative agents in the wild.

### Co-Gym (Simulated)
We use [TravelPlanner](https://github.com/OSU-NLP-Group/TravelPlanner) subset, arXiv CS paper subset curated in this work, [DiscoveryBench](https://github.com/allenai/discoverybench) subset for the simulated experiments on Travel Planning, Related Work, Tabular Analysis tasks respectively. See [`datasets/README.md`](datasets/README.md) for dataset details.

We use `gpt-4o` to simulate human behavior in our paper.

To reproduce our paper experiments:
1. Start Redis server: `docker run -d --name redis-stack -p 6379:6379 -p 8001:8001 redis/redis-stack:latest`
    - If you perfer to use Redis without the docker container (may need `sudo` permission):
      ```shell
      apt-get install redis
      systemctl start redis-server
      ```
2. Run the following command to test Fully Autonomous Agent:
    ```shell
    python -m scripts.fully_auto_agent_exp \
      --task {"travel_planning" or "related_work" or "tabular_analysis"} \
      --start-idx {start_idx_of_simualted_dataset} \
      --end-idx {end_idx_of_simulated_dataset} \
      --team-member-config-path {configs/teams/auto_agent_team_config_xxx.toml} \
      --result-dir-tag {result_dir_tag}
    ```
    - The result will be saved in `work_dir/{task}/{result-dir-tag}/results`.
3. Run the following command to test human-agent team:
    ```shell
    python -m scripts.collaborative_agent_exp \
      --task {"travel_planning" or "related_work" or "tabular_analysis"} \
      --start-idx {start_idx_of_simualted_dataset} \
      --end-idx {end_idx_of_simulated_dataset} \
      --team-member-config-path {"configs/teams/basic_coagent_simulated_user_team_config_xxx.toml" or "configs/teams/coagent_with_situational_planning_simulated_user_team_config_xxx.toml"} \
      --result-dir-tag {result_dir_tag}
    ```
    - The result will be saved in `work_dir/{task}/{result-dir-tag}/results`.

### Co-Gym (Real)
**We plan to release Co-Gym (Real) as a web research preview to the general public to better understand strengths and weakness of current LM agents as a teammate. The release is currently under review by Stanford Institutional Review Board (IRB). Stay tuned!**

## Evaluation
Co-Gym supports the evaluation of collaborative agents across both collaboration outcomes and processes.

### Evaluating Collaboration Outcome
We assess the collaboration outcome with both Delivery Rate and Task Performance (requires specifying task-specific scoring function to evaluate the outcome).

Co-Gym defines the **Collab**orative **Score** to jointly considering outcome delivery and quality:
```math
\text{Collab Score} = 1_{\text{Delivered}}\times\text{Task Performance}
```

To see the aggregated results, run the following command:
```shell
python scripts/report_simulated_result.py --result-dir {result_dir_that_include_result_folder_for_each_instance}
```

### Auditing Collaboration Process
Co-Gym analyze the collaboration process along the following dimensions:
- **Initiative Entropy:** This metric quantifies the distribution of initiative in the human-agent team, where a uniform distribution results in high score (with maximum as 1) and a skewed distribution results in a low score.
  - To compute, run: `python -m collaborative_gym.eval.initiative_analysis --result-dir {result_dir_that_include_result_folder_for_each_instance}`
- **Controlled Autonomy:** We measure this dimention by (1) counting the agent's confirmation questions that effectively eleicit a human responsee and (2) counting instances where the human verbally intervenes to halt the agent's actions.
  - To compute, run: `python -m collaborative_gym.eval.controlled_autonomy --result-dir {result_dir_that_include_result_folder_for_each_instance}`


## Add a New Agent
The current codebase supports three agents in `demo_agent/`:
- `demo_agent/auto_agent`: Fully Autonomous Agent that uses ReAct-style prompting and only consider task action space.
- `demo_agent/basic_collaborative_agent`: Collaborative Agent that uses ReAct-style prompting and consider both task action space and collaboration acts (i.e., `SendTeammateMessage`, `WaitTeammateContinue`).
- `demo_agent/collaborative_agent_with_situational_planning`: Collaborative Agent with Situational Planning which employs a two-stage decision-making approach when processing notifications. See Appendix B of [our paper](https://arxiv.org/abs/2412.15701) for details.

The simplest way to integrate an agent into Co-Gym is by ensuring compatibility with the `AgentNode` interface. `AgentNode` manages notifications from the environment and sends agent actions back via Redis, allowing you to focus on designing the agent's policy. To work with `AgentNode`, your agent should implement the following methods:
- `start(self, name: str, team_members: List[str], task_description: str, action_space: dict, example_question: str, example_trajectory: List) -> None`
  - This method is called when the task environment is initialized.
  - `name` is the name of the agent.
  - `team_members` is a list of team members in the session.
  - `task_description` is a string describing the task.
  - `action_space` is a list of actions. Each action is specified as a dictionary with the following keys:
    - `max_length`, `min_length`
    - `pattern`: Important for the agent to know what the format of the action should be.
    - `params`: Important for the agent to know what parameters are expected in the action.
    - `machine_readable_identifier`: A unique identifier for the action.
    - `human_readable_name`: A human-readable name for the action.
    - `human_readable_description`: A more detailed description of the action.
  - `example_question` is a string representing an example question for this task (if provided by the task environment).
  - `example_trajectory` is a list of Thought/Action/Updated Observation tuples representing an example trajectory for this task (if provided by the task environment). `example_question` and `example_trajectory` can help LM agent understand the task.
- `get_action(self, observation: Dict) -> str`
  - This method is called when the agent receives a new notification from the environment.
  - `observation` is a dictionary containing `event_log` and other task-specific observations.
  - The method should return a string representing the action to be taken following the format specified in `action_space`.
- `end(self, result_dir: str) -> None`
  - This method is called when the task is ended. The agent should clean up resources and save relevant information.


The agent can be implemented using any framework of your choice. Feel free to check out our example agents for reference.

## Contributions
If you have any questions or suggestions, please feel free to open an issue or pull request. We welcome contributions to add more task environments & agents and improve the codebase!

Contact person: [Yijia Shao](mailto:shaoyj@stanford.edu), [Vinay Samuel](mailto:vsamuel@andrew.cmu.edu), and [Yucheng Jiang](mailto:yuchengj@stanford.edu)

## Acknowledgement
The development of Co-Gym won't be possible without these open-source projects:
- [Gymnasium](https://github.com/Farama-Foundation/Gymnasium): for defining API standard for single-agent reinforcement learning environments.
- [storm](https://github.com/stanford-oval/storm): for providing LM modules, retriever modules, and workflows for knowledge-intensive writing tasks.
- [aact](https://github.com/ProKil/aact): for supporting asynchronous communications between nodes (i.e., humans, agents, environments in this project).

We are very grateful to the following amazing designers who have contributed to this project:
- Co-Gym (Real) UI design: Yanan Zhang
- Logo design: Long Lin

## Citation
Please cite our paper if you use this code or part of it in your work:
```
@misc{shao2024collaborativegym,
      title={Collaborative Gym: A Framework for Enabling and Evaluating Human-Agent Collaboration}, 
      author={Yijia Shao and Vinay Samuel and Yucheng Jiang and John Yang and Diyi Yang},
      year={2024},
      eprint={2412.15701},
      archivePrefix={arXiv},
      primaryClass={cs.AI},
      url={https://arxiv.org/abs/2412.15701}, 
}
```
