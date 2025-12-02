# Pentestagent Workflow

## Prerequisites

Make sure you have [uv](https://docs.astral.sh/uv/) installed on your system. If you don't have it installed, you can install it using:

```bash
# On macOS, Linux, and WSL
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Generating Katana result file:

```bash
katana -u https://example.com/ -output example.com.txt -xhr -fx -jsonl -omit-body -omit-raw -H tools/web_requester/headers.txt -cos tools/web_requester/out_of_scope.txt -delay 10 -headless -no-sandbox -timeout 300 -d 3 -jc -sf qurl -kf -ef css,png,jpg,bmp,ico,gif,svg,otf,pdf,map,woff,ttf
```

## Project Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd pentestagent-workflow
```

2. Install dependencies using uv:
```bash
uv sync
```

This command will:
- Create a virtual environment automatically
- Install all dependencies specified in `pyproject.toml`
- Generate/update the `uv.lock` file for reproducible builds

## Docker commands

1. Build the docker image:
```bash
docker build -t autopentester:latest
```

2. Initial run of the container from the image:
```bash
docker run -it --name autopentester --hostname autopentester --cap-add=NET_ADMIN --privileged --sysctl net.ipv6.conf.all.disable_ipv6=0 autopentester:latest
```

3. Subsequent run of previously created container:
```bash
docker start autopentester && docker attach autopentester
```

### Alternative Installation Methods

If you prefer to use requirements.txt:
```bash
uv pip install -r requirements.txt
```

Or to install in development mode:
```bash
uv pip install -e .
```

## Running the Project

### Using uv (Recommended)

Run the main application directly with uv:
```bash
uv run python main.py
```

This automatically activates the virtual environment and runs the script.

### Manual Environment Activation

Alternatively, you can activate the virtual environment manually:
```bash
# On macOS/Linux
source .venv/bin/activate

# On Windows
.venv\Scripts\activate

# Then run the main file
python main.py
```

## Running Tests

### Running All Tests

To run all tests in the project:
```bash
uv run pytest
```

### Running Specific Test Files

To run a specific test file:
```bash
uv run pytest tests/test_serper_search.py
```

### Running Tests with Verbose Output

For more detailed test output:
```bash
uv run pytest -v
```

### Running Tests with Coverage

To run tests with coverage reporting:
```bash
uv run pytest --cov=.
```

### Additional Pytest Options
- Show print outputs: `uv run pytest -s`
- Run tests in parallel: `uv run pytest -n auto` (requires pytest-xdist)
- Run only failed tests: `uv run pytest --lf`
- Stop on first failure: `uv run pytest -x`
- Run tests matching a pattern: `uv run pytest -k "test_pattern"`

## Development

### Adding New Dependencies

To add new dependencies to the project:
```bash
uv add package-name
```

For development dependencies:
```bash
uv add --dev package-name
```

### Updating Dependencies

To update all dependencies:
```bash
uv sync --upgrade
```

## Project Structure

```
pentestagent-workflow/
├── main.py              # Main application entry point
├── pyproject.toml       # Project configuration and dependencies
├── uv.lock             # Lock file for reproducible builds
├── custom_agents/      # Custom agent implementations
├── tools/              # Utility tools and functions
    └── web_requester   # Web requester and its dependencies
└── tests/              # Test files
    └── test_serper_search.py
.env
Dockerfile
entrypoint.sh
README.md
```
# Pentest Workflow Orchestration

This project implements an asynchronous, agent-driven penetration testing (pentest) workflow with task orchestration, state persistence, and error handling. It integrates multiple tools and custom agents to perform reconnaissance, vulnerability identification, and exploitation, while managing session state reliably.

---

## Overview

The pentest workflow is designed as a sequence of **tasks** representing discrete units of work (e.g., running Katana, reconnaissance, exploitation). These tasks are processed synchronously with retry and error handling mechanisms. The system persists state to a SQLite database, allowing for session recovery and tracking.

---

## Key Components

### GlobalState: Centralized Task and Session State Management

The `GlobalState` class is a Pydantic model that encapsulates the entire state of a pentest session, including its goals, target, and the list of tasks being managed. It acts as the in-memory representation of the session's current state, which is periodically persisted to the database.

#### Attributes

- `goal` (`str`): The overall objective of the pentest session, defined by the user.
- `target` (`str`): The target entity or system under test.
- `task_list` (`Dict[str, Task]`): A dictionary mapping task UUID strings to their corresponding `Task` objects.
- `task_name_index` (`Dict[str, List[str]]`): An index mapping task names (e.g., `"run_katana"`) to lists of task UUIDs, enabling efficient retrieval of tasks by name.

#### Methods

### `add_task(task: Task)`

Adds a new `Task` object to the `GlobalState`.

- Inserts the task into the `task_list` dictionary using its UUID as the key.
- Updates the `task_name_index` to include the new task UUID under its task name.
- Ensures efficient tracking and lookup of tasks by their names.

### `update_task(**updates)`

Dynamically updates fields of an existing task within the state.

- Requires the `uuid` of the task to identify which task to update.
- Accepts any other task field updates as keyword arguments.
- Raises `ValueError` if the task UUID does not exist or if an invalid field name is provided.
- After updating, the task is re-validated by reconstructing the `Task` object to ensure data integrity.

Example usage:

```python
global_state.update_task(uuid="some-uuid", status=TaskStatus.COMPLETED, result="Success")
```

### `get_tasks_by_name(name: str) -> List[Task]`

Retrieves all tasks in the current global state that have the specified task name.

- **Parameters:**
  - `name` (`str`): The name of the task(s) to retrieve (e.g., `"run_katana"`).

- **Returns:**
  - `List[Task]`: A list of `Task` objects that have the given name.
    - If no tasks match, returns an empty list.

- **How it works:**
  - Looks up the task UUIDs associated with the provided task name in the `task_name_index` dictionary.
  - Uses these UUIDs to fetch the corresponding `Task` objects from the `task_list`.
  
- **Use case:**
  - Useful when you want to get all tasks of a certain type (e.g., all reconnaissance tasks) to check their status or results.

**Example:**

```python
recon_tasks = global_state.get_tasks_by_name("run_katana")
for task in recon_tasks:
    print(task.status, task.result)
```

### Task Management

- **Tasks** are instances of the `Task` class, defined with properties such as:
  - `uuid`: The unique uuid of the task in string format.
  - `name`: The identifier of the task (e.g., `"run_katana"`, `"run_recon_agent"`).
  - `args` and `kwargs`: Arguments to the task function.
  - `status`: Current status (`PENDING`, `IN_PROGRESS`, `COMPLETED`, `FAILED`).
  - `result`: Output of the task execution.
  - `retry_counter`: Number of retries attempted.
  - `stage`: Workflow stage (e.g., `RECON`, `EXPLOIT`, `MAP_ATTACK`, `REPORT`).
  - `additional_instructions`: Additional instructions to be passed to the agent.

- **Task functions** are mapped in `TASK_FUNCTIONS`, linking task names to their executing functions.

### Session Management

- Each pentest run is associated with a unique **session ID** (UUID string).
- Sessions are persisted to a SQLite database with methods like:
  - `create_session(session_id)`
  - `save_current_global_state(session_id, global_state)`
  - `update_task_in_global_state(session_id, task)`
  - `add_task_in_global_state(session_id, task)`

---

## Workflow Execution

### Task Execution (`run_task`)

- When a task is run:
  1. Its status is updated to `IN_PROGRESS`.
  2. The corresponding function is invoked (async or sync).
  3. On success, result is saved and status is set to `COMPLETED`.
  4. On failure, status is set to `FAILED` and error details are saved.
  5. All status updates are persisted to the session's global state.

### Task Routing (`TASK_ROUTER`)

- After task completion, subsequent tasks are generated based on the results:
  - `run_katana` → triggers `run_recon_agent` with Katana output.
  - `run_recon_agent` → generates exploitation tasks per detected vulnerabilities.
  - Additional mappings for other tasks like reporting, etc.

- The router function for reconnaissance tasks (`route_indiv_exploit_tasks`) analyzes detected vulnerabilities and returns new tasks for exploitation agents specialized per vulnerability type (SQLi, XSS, XXE, SSRF, Deserialization).

### Retry Logic

- Failed tasks are retried up to 3 times, with a delay between retries.
- If a task fails after max retries, the workflow terminates early.

### Async Workflow Loop (`run_pentest_workflow`)

- Processes a queue of tasks asynchronously.
- Tasks are added, removed, and re-queued dynamically.
- Graceful interruption handling: tasks can be paused/resumed with Ctrl+C.
- Ensures persistence and state updates after each task run.

---

## Starting a Session

- **New sessions** are initialized with user prompts for:
  - Target (e.g., IP address, domain)
  - Goal (e.g., find SQL injection vulnerabilities)

- The first task (`run_katana`) is seeded with the target and added to the tasks queue and session state.

---

## Interrupt Handling

- The workflow listens for SIGINT (Ctrl+C):
  - On first interrupt, the workflow pauses.
  - The user can optionally enter a new prompt to continue or exit.
  - On a second interrupt, the program terminates cleanly.

---

## How to Run

1. **Initialize the database**:
    ```python
    init_db()
    ```
2. ** Run the main event loop**:
    ```python
    asyncio.run(main_loop())
    ```
3. The CLI will prompt to start new sessions and continue existing ones.

# Common Tools

# web_requester:
Executes a web request to the specified URL using either the requests or Selenium method.
This function is designed for robust scraping or automation contexts, including detection 
and mitigation of WAFs, CAPTCHAs, rate limits, and connection issues.

It performs up to 5 attempts per HTTP request, 10 redirects for HTTP requests that triggers redirects and waits up to 6 seconds (1.5s x 4) per NordVPN connection attempt

How to pass as a tool to an agent:
```
agent = Agent(
    name="...",
    role="...",
    tools=[
        ShellTools(cache_results=True),
        WebRequesterTool(cache_results=True, start_with_vpn=False, use_vpn=True, proxies = proxies),
        update_task_result,
        get_goal,
        get_target,
        get_user_input,
    ],
)

`start_with_vpn`: bool = True - indicates you want to connect to VPN prior to the scan. Default: False
`use_vpn`: bool = True - indicates you want to rotate VPN IP when encountering issues. Default: True
`proxies`: dict = {"http":"172.2.2.2:8080","https":"172.2.2.2:8080"} Set proxy for HTTP and HTTPS requests. Default: None
`use_requests`: bool = True - Use True for now, which uses python requests. Setting to False will use Selenium headless browser (safer) but it is not fully implemented. Default: True
`max_redirects`: int = 10 - Sets the max number of redirections allowed, sometimes website can redirect infinitely. Default: 10

```

To customize HTTP request:
if you want to send a request with Content-Type: application/x-www-form-urlencoded but with JSON body:
```
headers = {
    Content-Type: application/x-www-form-urlencoded
}
data = '{"aaa":"bbb","ccc":"ddd"}'
```
if you want to send a request with Content-Type: application/json but with JSON body:
```
data = {"aaa":"bbb","ccc":"ddd"}
```
if you want to send a request with Content-Type: application/json but with normal data body:
```
headers = {
    Content-Type: application/json
}
data = dedent("""\
aaa=bbb&ccc=ddd
&eee=fff
""")
```

Under the hood:

    Args:
        url (str): The target URL to send the request to.
        method (str, optional): The HTTP method to use (e.g., 'GET', 'POST'). Defaults to 'GET'.
        headers (dict, optional): Dictionary of HTTP headers to include in the request. Defaults to None.
        data (dict, optional): Data payload for POST/PUT requests. Defaults to None.
        proxies (dict, optional): Dictionary of proxies to route the request through. Defaults to None.
        use_requests (bool, optional): Whether to use the `requests` library or Selenium for the request. Defaults to True.
        max_redirects (int, optional): Maximum number of redirects to follow. Defaults to 10.

    Returns:
        dict: On success, returns a dictionary containing `RequestDetails` and `ResponseDetails`.
        RequestDetails contains:
            - 'method': str - HTTP method used
            - 'url': str - URL requested
            - 'request_headers': Dict[str, str] - The headers sent with the request
            - 'request_body': str - The body sent with the request (if any)
            - 'response_headers': Response headers
            - 'response_body': Raw response content
        If an error occurs, returns a dictionary with:
            - 'url': The URL attempted
            - 'status_code': None
            - 'error': Error message explaining the failure

    Notes:
        - If `use_requests` is True, the request is executed via `fetch_with_requests`.
        - If False, the request is executed via Selenium (`fetch_with_selenium`), allowing
        rendering of dynamic pages and evasion of JavaScript-heavy blocking.
        - Some advanced behavior like CAPTCHA/WAF detection, timeouts, and VPN rotation are present
        in the logic but currently commented out for manual control or future use.
