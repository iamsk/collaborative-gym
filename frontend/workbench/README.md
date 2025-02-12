# Collaborative Gym User Interface

## Setup
1. Make a copy of `.env.example` and name it `.env`. Fill in the required information.
2. Install the required packages by running `pnpm install`.
    - If you don't have `pnpm` installed, you can install it with `npm install -g pnpm`.


## Running Collaborative Gym with User Interface
1. Start the Redis server that is used for communication between human, agent, and task environment: `docker run -d --name redis-stack -p 6379:6379 -p 8001:8001 redis/redis-stack:latest`
    - If you prefer to use Redis without the docker container (may need `sudo` permission):
      ```shell
      apt-get install redis
      systemctl start redis-server
      ```
2. Start the Co-Gym server by running the following command under the root directory:
    ```shell
   DISABLE_AGENT={true/false} uvicorn collaborative_gym.server:app --reload
    ```
   - The server will be running at `ws://localhost:8000`. If it's not; you need to change `NEXT_PUBLIC_API_URL` and `NEXT_PUBLIC_WS_URL` in `.env` accordingly. It is important that you use Google Chrome to run Co-Gym (Real) Locally
   - When developing the UI feature, it's suggested to set `DISABLE_AGENT` as `true`. This will disable starting agent node when a new session launches in the backend, so that you can concentrate on frontend features.
   - If `DISABLE_AGENT` is `false`, the server starts a `gui_user` node and an `agent_node`. You can adjust the `start_node_base_command` for `agent_node` to use a different agent.
        ```python
        # team members
        [
            TeamMemberConfig(name=f"user_{user_id}", type="gui_user", start_node_base_command=""),
            TeamMemberConfig(name=AGENT_NAME, type="agent", start_node_base_command="python -m demo_agent.collaborative_agent_with_situational_planning.agent --model-name gpt-4o --wait-time 1 --enhance-user-control")
        ]
        ```
3. Start the Next.js development server by running `pnpm dev` under the current directory.


## Frontend Code Structure
The frontend is built with Next.js 13+ using the App Router pattern. Here's the main structure:

```scss
frontend/deployed/
├── app/                    # Next.js app directory (App Router)
│   ├── (session)/          # session/[id]/page.tsx defines the session page, session/[id]/evaluation/page.tsx defines the result eval page
│   ├── page.tsx            # Landing page
├── components/             # Reusable React components
│   ├── chat/               # Chat interface components
│   ├── evaluation/         # Evaluation interface components
│   ├── tools/              # Task-specific tools (Jupyter, Paper Search, etc.)
│   ├── ui/                 # Base UI components (buttons, dialogs, etc.) Please prioritize using Material UI components; only use components here if they are better suited
│   └── workspace/          # Task-specific workspace interfaces
|   └── co-workbench.tsx    # The main component for the session page
|   └── landing-page.tsx    # The main component for the session page
├── context/
│   ├── session.tsx         # TaskSessionProvider that maintains envId across different components
│   ├── socket.tsx          # WebSocketProvider that exposes a websocket for bi-directional communication
├── lib/                    # Utility functions and type definitions
│   ├── actions.ts          # Actions (important: need to match collaborative_gym/env)
│   ├── api.ts              # API client functions (important: need to match collaborative_gym/server.py)
└── prisma/                 # Database schema and client (usually no need to change)
```

## Add Workspace for a New Task Environment
1. **Create the Interface Component:** Add a new interface component file under `components/workspace/`. Refer to existing files for examples.
2. **Update the Landing Page:**
    - Add the new task to pages in `components/landing-page.tsx`.
    - Modify the `selectedTab` logic to handle task selection.
3. **Use the Interface Component in Co-Workbench:** Include the new interface component in `components/co-workbench.tsx`.
4. **Handle Task Arguments for Starting a Session:** Implement logic to obtain the necessary arguments for the new task in `lib/start-session.ts`.

