import json
from typing import Dict, List, Optional

from collaborative_gym.utils.code_executor import JupyterManager


class ContextProcessor:
    @staticmethod
    def observation_to_str(obs: Dict):
        """Expecting the observation to be a dictionary."""
        trimmed_obs = {}
        for k in obs:
            if "jupyter" in k:
                exe_history = JupyterManager.str_to_execution_history(obs[k])
                if len(exe_history) == 0:
                    trimmed_obs[k] = "No code execution history"
                elif len(exe_history) > 5:  # Only show the last 5 entries
                    history = f"...{len(exe_history) - 5} more code execution history entries not shown...\n"
                    for cell in exe_history[-5:]:
                        code_block = cell["code"]
                        code_result = cell["result"]
                        try:
                            code_result_str = code_result.output.strip()
                            if "\n['" in code_result_str:
                                code_result_str = code_result_str.split("\n['")[0]
                            history += f"Code block:\n{code_block.code.strip()}\n"
                            history += f"Output:\n{code_result_str}\n\n"
                        except Exception as e:
                            history += f"Code block:\n{code_block}\n"
                            history += f"Output:\n{code_result}\n\n"
                    trimmed_obs[k] = history.strip()
                else:
                    trimmed_obs[k] = obs[k]
            else:
                trimmed_obs[k] = obs[k]
        return json.dumps(trimmed_obs, indent=4)

    @staticmethod
    def chat_history_to_str(current_role: str, chat_history: list):
        """Expecting the chat history to be a list of dictionaries containing 'role' and 'message'."""
        if len(chat_history) == 0:
            return "No chat history"
        s = ""
        for turn in chat_history:
            role = turn["role"]
            if role == current_role:
                role += " (You)"
            s += f"{role}: {turn['message']}\n"
        return s

    @staticmethod
    def action_space_to_str(
        action_space: dict, excluded_action_names: Optional[List[str]] = None
    ):
        """Expecting the action space to be a dictionary.

        Args:
            action_space (dict): The action space dictionary.
            excluded_action_names (list): The list of human-readable names of actions to exclude from the description.
        """
        if excluded_action_names is None:
            excluded_action_names = []
        action_space_description = []
        for space in action_space:
            if space["human_readable_name"] in excluded_action_names:
                continue
            action_desc_str = (
                f'{space["human_readable_name"]} (Parameters: {space["params"]})'
            )
            action_desc_str += f'\n- Description: {space["human_readable_description"]}'
            action_desc_str += (
                f"\n- Regex pattern for the action "
                f'(your output needs to follow this if you take this action): {space["pattern"]}'
            )
            action_space_description.append(action_desc_str)
        return "\n\n".join(action_space_description)

    @staticmethod
    def task_example_to_str(example_question: str, example_trajectory: List):
        """Expecting the example trajectory to be a list of tuples containing (thought, action, updated_obs)."""
        s = f"Query: {example_question}\n"
        for thought, action, updated_obs in example_trajectory:
            s += f"Thought: {thought}\nAction: {action}\n\n"
        return s

    @staticmethod
    def action_history_to_str(action_history: list, max_history_length: int = 5):
        """Expecting the action history to be a list of strings."""
        if len(action_history) == 0:
            return "No action history"
        return "\n".join(action_history[-max_history_length:])
