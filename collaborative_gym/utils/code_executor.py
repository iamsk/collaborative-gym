import atexit
import base64
import json
import logging
import os.path
import re
import secrets
import uuid
from collections import deque
from pathlib import Path
from types import TracebackType
from typing import Optional, Dict, Union, List, Deque, Self, Type

import docker
from autogen.coding import MarkdownCodeExtractor
from autogen.coding.base import (
    IPythonCodeResult,
    CodeBlock,
    CodeExecutor,
    CodeExtractor,
)
from autogen.coding.docker_commandline_code_executor import _wait_for_ready
from autogen.coding.jupyter import (
    DockerJupyterServer,
    JupyterConnectable,
    JupyterConnectionInfo,
)
from autogen.coding.utils import silence_pip
from tenacity import stop_after_attempt, retry, wait_exponential

from collaborative_gym.utils.jupyter_client import JupyterClient


class CustomDockerJupyterServer(DockerJupyterServer):
    """Wrapper around DockerJupyterServer to allow for custom mounting of volumes."""

    def __init__(
        self,
        *,
        custom_image_name: Optional[str] = None,
        container_name: Optional[str] = None,
        auto_remove: bool = True,
        stop_container: bool = True,
        docker_env: Dict[str, str] = {},
        token: Union[
            str, DockerJupyterServer.GenerateToken
        ] = DockerJupyterServer.GenerateToken(),
        local_directory: Optional[str] = None,
        container_directory: Optional[str] = None,
        device_requests: Optional[List] = None,
    ):
        """Most part of the code is borrowed from the parent class DockerJupyterServer.

        Start a Jupyter kernel gateway server in a Docker container.

        Args:
            custom_image_name (Optional[str], optional): Custom image to use. If this is None,
                then the bundled image will be built and used. The default image is based on
                quay.io/jupyter/docker-stacks-foundation and extended to include jupyter_kernel_gateway
            container_name (Optional[str], optional): Name of the container to start.
                A name will be generated if None.
            auto_remove (bool, optional): If true the Docker container will be deleted
                when it is stopped.
            stop_container (bool, optional): If true the container will be stopped,
                either by program exit or using the context manager
            docker_env (Dict[str, str], optional): Extra environment variables to pass
                to the running Docker container.
            token (Union[str, GenerateToken], optional): Token to use for authentication.
                If GenerateToken is used, a random token will be generated. Empty string
                will be unauthenticated.
            local_directory (Optional[str], optional): Local directory to mount to the container.
            container_directory (Optional[str], optional): Directory in the container to mount.
            device_requests (Optional[List], optional): Expose host resources such as GPUs to the container,
                as a list of :py:class:`docker.types.DeviceRequest` instances.
        """
        if container_name is None:
            container_name = f"co-gym-jupyter-{uuid.uuid4()}"

        client = docker.from_env()
        if custom_image_name is None:
            raise ValueError("Custom image name must be provided")
        else:
            image_name = custom_image_name
            # Check if the image exists
            try:
                client.images.get(image_name)
            except docker.errors.ImageNotFound:
                raise ValueError(f"Custom image {image_name} does not exist")

        if isinstance(token, DockerJupyterServer.GenerateToken):
            self._token = secrets.token_hex(32)
        else:
            self._token = token

        # Run the container
        env = {"TOKEN": self._token}
        env.update(docker_env)
        # New code to mount a local directory to the container starts here
        volumes = {}
        if local_directory:
            if not os.path.exists(local_directory):
                os.makedirs(local_directory)
            os.chmod(local_directory, 0o777)  # Ensure the directory is writable.
            container_directory = (
                container_directory or "/home/jovyan/work"
            )  # Default directory.
            volumes[local_directory] = {"bind": container_directory, "mode": "rw"}
        self.volumes = volumes
        # New code to mount a local directory to the container ends here
        container = client.containers.run(
            image_name,
            detach=True,
            auto_remove=auto_remove,
            environment=env,
            publish_all_ports=True,
            name=container_name,
            volumes=volumes,
            device_requests=device_requests,
        )
        _wait_for_ready(container)
        container_ports = container.ports
        self._port = int(container_ports["8888/tcp"][0]["HostPort"])
        self._container_id = container.id

        def cleanup() -> None:
            try:
                inner_container = client.containers.get(container.id)
                inner_container.stop()
            except docker.errors.NotFound:
                pass

            atexit.unregister(cleanup)

        if stop_container:
            atexit.register(cleanup)

        self._cleanup_func = cleanup
        self._stop_container = stop_container


class CustomJupyterCodeExecutor(CodeExecutor):
    """Adapted from https://github.com/timrbula/autogen/blob/main/autogen/coding/jupyter/jupyter_code_executor.py"""

    def __init__(
        self,
        jupyter_server: Union[JupyterConnectable, JupyterConnectionInfo],
        kernel_name: str = "python3",
        timeout: int = 60,
        output_dir: Union[Path, str] = Path("."),
        max_retries: int = 2,
        max_history: int = 100,  # Maximum number of cells to keep in history
    ):
        if timeout < 1:
            raise ValueError("Timeout must be greater than or equal to 1.")

        if isinstance(output_dir, str):
            output_dir = Path(output_dir)

        if not output_dir.exists():
            raise ValueError(f"Output directory {output_dir} does not exist.")

        if isinstance(jupyter_server, JupyterConnectable):
            self._connection_info = jupyter_server.connection_info
        elif isinstance(jupyter_server, JupyterConnectionInfo):
            self._connection_info = jupyter_server
        else:
            raise ValueError(
                "jupyter_server must be a JupyterConnectable or JupyterConnectionInfo."
            )

        self._jupyter_client = JupyterClient(self._connection_info)
        available_kernels = self._jupyter_client.list_kernel_specs()
        if kernel_name not in available_kernels["kernelspecs"]:
            raise ValueError(f"Kernel {kernel_name} is not installed.")

        self._kernel_id = self._jupyter_client.start_kernel(kernel_name)
        self._kernel_name = kernel_name
        self._jupyter_kernel_client = self._jupyter_client.get_kernel_client(
            self._kernel_id
        )
        self._timeout = timeout
        self._output_dir = output_dir

        self.max_retries = max_retries
        self._execution_history: Deque[CodeBlock] = deque(maxlen=max_history)
        self._skip_history = False  # Flag to prevent infinite recursion

    @property
    def code_extractor(self) -> CodeExtractor:
        """Copied from https://github.com/timrbula/autogen/blob/main/autogen/coding/jupyter/jupyter_code_executor.py
        JupyterCodeExecutor

        (Experimental) Export a code extractor that can be used by an agent."""
        return MarkdownCodeExtractor()

    def restart(self) -> None:
        """Copied from https://github.com/timrbula/autogen/blob/main/autogen/coding/jupyter/jupyter_code_executor.py
        JupyterCodeExecutor

        (Experimental) Restart a new session."""
        self._jupyter_client.restart_kernel(self._kernel_id)
        self._jupyter_kernel_client = self._jupyter_client.get_kernel_client(
            self._kernel_id
        )

    def stop(self) -> None:
        """Copied from https://github.com/timrbula/autogen/blob/main/autogen/coding/jupyter/jupyter_code_executor.py
        JupyterCodeExecutor

        Stop the kernel."""
        self._jupyter_client.delete_kernel(self._kernel_id)

    def __enter__(self) -> Self:
        """Copied from https://github.com/timrbula/autogen/blob/main/autogen/coding/jupyter/jupyter_code_executor.py
        JupyterCodeExecutor"""
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        """Copied from https://github.com/timrbula/autogen/blob/main/autogen/coding/jupyter/jupyter_code_executor.py
        JupyterCodeExecutor"""
        self.stop()

    def _add_to_history(self, code_block: CodeBlock):
        """Add executed code block to history."""
        self._execution_history.append(code_block)

    def _rerun_history(self) -> bool:
        """Rerun all previous cells after restart.

        Returns:
            bool: True if history rerun was successful, False otherwise
        """
        if self._skip_history:
            return True

        try:
            self._skip_history = True  # Prevent recursive history replay
            logging.info("Rerunning previous cells after kernel restart...")

            for i, code_block in enumerate(self._execution_history):
                logging.info(f"Rerunning cell {i + 1}/{len(self._execution_history)}")
                result = self._jupyter_kernel_client.execute(
                    silence_pip(code_block.code, code_block.language),
                    timeout_seconds=self._timeout,
                )
                if not result.is_ok:
                    logging.error(f"Failed to rerun cell {i + 1}: {result.output}")
                    return False

            logging.info("Successfully reran all previous cells")
            return True

        except Exception as e:
            logging.error(f"Error during history rerun: {str(e)}")
            return False
        finally:
            self._skip_history = False

    def _ensure_kernel_connection(self):
        """Ensure kernel connection is alive, restart if necessary."""
        # FIXME: rerun is costly. Hacky fix for now as the connection is lost after being idle for a while.
        try:
            self._jupyter_kernel_client.wait_for_ready()
        except (BrokenPipeError, ConnectionError) as e:
            logging.warning(
                f"Connection error occurred: {str(e)}. Attempting to reset kernel client."
            )
            try:
                # Try to restart the kernel
                self.restart()
                # Get a fresh kernel client
                self._jupyter_kernel_client = self._jupyter_client.get_kernel_client(
                    self._kernel_id
                )
                self._jupyter_kernel_client.wait_for_ready()

                # Rerun previous cells
                if not self._rerun_history():
                    raise RuntimeError(
                        "Failed to rerun previous cells after kernel restart"
                    )

                logging.info("Kernel client reset and history restored successfully.")
            except Exception as e:
                logging.error(f"Failed to reset kernel client: {str(e)}")
                raise

    @retry(
        stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def _execute_with_retry(self, code: str) -> IPythonCodeResult:
        """Execute code with retry logic."""
        try:
            self._ensure_kernel_connection()
            result = self._jupyter_kernel_client.execute(
                code, timeout_seconds=self._timeout
            )
            return result
        except Exception as e:
            logging.error(f"Error executing code: {str(e)}")
            if "Connection to remote host was lost" in str(e):
                # Force a kernel restart on connection loss
                self.restart()
                # Rerun history will be handled by _ensure_kernel_connection on next retry
                raise  # Let retry logic handle it
            raise

    @staticmethod
    def filter_cell_output(output):
        """Filter out warnings, progress bars from the output."""
        lines = output.split("\n")
        ignore_patterns = [
            r"^.*TqdmExperimentalWarning:.*$",
            r"^.*from tqdm.*$",
            r'^{"version_major":.*}$',
            r"^.*FutureWarning:.*$",
            r"^.*warnings.warn.*$",
            r"^.*\d+%\|.*$",
        ]

        combined_pattern = "|".join(ignore_patterns)
        cleaned_lines = [line for line in lines if not re.match(combined_pattern, line)]
        cleaned_output = "\n".join(cleaned_lines).strip()

        return cleaned_output

    @staticmethod
    def clean_code(code_string):
        """Clean machine-generated code by:
        1. Converting double backslashes to single backslashes
        2. Converting \\n to actual newlines
        3. Removing extra escapes from quotes
        4. Fixing path separators
        """
        # Convert \\\\ to \\ (in case of quadruple backslashes)
        code_string = code_string.replace("\\\\", "\\")
        # Convert \\n to actual newlines
        code_string = code_string.replace("\\n", "\n")
        # Remove unnecessary escapes from quotes
        code_string = code_string.replace("\\'", "'")
        code_string = code_string.replace('\\"', '"')
        # Fix path separators
        code_string = code_string.replace("\\/", "/")
        # Handle any remaining double backslashes
        code_string = code_string.replace("\\\\", "\\")

        return code_string

    def _save_image(self, image_data_base64: str) -> str:
        """Save image data to a file."""
        image_data = base64.b64decode(image_data_base64)
        # Randomly generate a filename.
        filename = f"{uuid.uuid4().hex}.png"
        path = os.path.join(self._output_dir, filename)
        with open(path, "wb") as f:
            f.write(image_data)
        # return os.path.abspath(path)
        return filename

    def _save_html(self, html_data: str) -> str:
        """Save html data to a file."""
        # Randomly generate a filename.
        filename = f"{uuid.uuid4().hex}.html"
        path = os.path.join(self._output_dir, filename)
        with open(path, "w") as f:
            f.write(html_data)
        # return os.path.abspath(path)
        return filename

    def execute_code_blocks(self, code_blocks: List[CodeBlock]) -> IPythonCodeResult:
        """Execute code blocks with enhanced error handling and history tracking."""
        outputs = []
        output_files = []

        for code_block in code_blocks:
            code_block.code = self.clean_code(code_block.code)
            code = silence_pip(code_block.code, code_block.language)
            try:
                result = self._execute_with_retry(code)

                if result.is_ok:
                    # Only add to history if execution was successful and we're not replaying history
                    if not self._skip_history:
                        self._add_to_history(code_block)

                    outputs.append(self.filter_cell_output(result.output))
                    for data in result.data_items:
                        if data.mime_type == "image/png":
                            path = self._save_image(data.data)
                            outputs.append(f"Image data saved to {path}")
                            output_files.append(path)
                        elif data.mime_type == "text/html":
                            path = self._save_html(data.data)
                            outputs.append(f"HTML data saved to {path}")
                            output_files.append(path)
                        else:
                            try:
                                outputs.append(json.dumps(data.data))
                            except Exception as e:
                                logging.error(f"Error processing data item: {str(e)}")
                                outputs.append(str(data.data))
                else:
                    return IPythonCodeResult(
                        exit_code=1,
                        output=f"ERROR: {result.output}",
                    )
            except Exception as e:
                error_msg = f"Failed to execute code block after {self.max_retries} attempts: {str(e)}"
                logging.error(error_msg)
                return IPythonCodeResult(
                    exit_code=1,
                    output=error_msg,
                )

        return IPythonCodeResult(
            exit_code=0,
            output="\n".join([str(output) for output in outputs]),
            output_files=output_files,
        )

    def clear_history(self):
        """Clear the execution history."""
        self._execution_history.clear()

    def get_history_size(self) -> int:
        """Get the number of cells in the execution history."""
        return len(self._execution_history)


class JupyterManager:
    def __init__(
        self,
        *,
        custom_image_name: Optional[str] = None,
        container_name: Optional[str] = None,
        docker_volume_local_dir: Optional[str] = None,
        device_requests: Optional[List] = None,
        timeout: int = 60,
    ):
        self.docker_volume_local_dir = docker_volume_local_dir
        self.docker_server = CustomDockerJupyterServer(
            custom_image_name=custom_image_name,
            container_name=container_name,
            local_directory=docker_volume_local_dir,
            device_requests=device_requests,
        )
        self.jupyter_executor = CustomJupyterCodeExecutor(
            self.docker_server, output_dir=docker_volume_local_dir, timeout=timeout
        )

        self.code_blocks = []
        self.code_results = []

    def close(self):
        self.jupyter_executor.stop()

    def reset(self):
        self.jupyter_executor.restart()
        self.code_blocks = []
        self.code_results = []

    def execute_python_code(self, code: str) -> IPythonCodeResult:
        code_block = CodeBlock(language="python", code=code)
        code_result = self.jupyter_executor.execute_code_blocks([code_block])
        self.code_blocks.append(code_block)
        self.code_results.append(code_result)

        return code_result

    def execution_history_to_str(self):
        history = ""
        for code_block, code_result in zip(self.code_blocks, self.code_results):
            code_result_str = code_result.output.strip()
            if "\n['" in code_result_str:
                code_result_str = code_result_str.split("\n['")[0]
            history += f"Code block:\n{code_block.code.strip()}\n"
            history += f"Output:\n{code_result_str}\n\n"

        return history.strip()

    @staticmethod
    def str_to_execution_history(history: str):
        code_blocks = []
        code_results = []
        for block in history.split("Code block:")[1:]:
            code_block, code_result = block.split("Output:")
            code_blocks.append(code_block.strip())
            code_results.append(code_result.strip())

        execution_history = []
        for code_block, code_result in zip(code_blocks, code_results):
            execution_history.append({"code": code_block, "result": code_result})

        return execution_history
