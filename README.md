# python-backend-tutorial

The smallest useful chatbot backend: send a message, get a reply.
Python 3.14, FastAPI, uv, models served by [Nebius Token Factory](https://tokenfactory.nebius.com/)
(OpenAI-API compatible, so it is driven with the `openai` SDK).

No database, no conversation history, no middleware — the agent, and a cookie in front of it.

## Run

```bash
cp .env.example .env                       # configuration
cp .env.secrets.example .env.secrets       # credentials — fill these in
uv run fastapi dev app/main.py
```

Two files on purpose: `.env` is ordinary configuration and `.env.secrets` holds the three
credentials (`NEBIUS_API_KEY`, `SESSION_SECRET`, `AUTH_PASSWORD`). Both are gitignored, both
examples are committed. Splitting them means the file you paste into a terminal, a support
thread or a bug report is the harmless one, and in production the secrets file is the only thing
your secret manager has to mount. `Settings` reads both, secrets last, so a secret can never be
shadowed by the config file.

Interactive OpenAPI docs: <http://127.0.0.1:8000/docs>

Lint and format with [ruff](https://docs.astral.sh/ruff/) — one tool for both:

```bash
uv run ruff check --fix    # lint, autofixing what it safely can
uv run ruff format         # format
```

Every `/chat` call needs a session cookie, so log in first and keep the cookie jar:

```bash
curl -sX POST localhost:8000/auth/login -c jar.txt -H 'content-type: application/json' \
     -d '{"username":"demo","password":"<AUTH_PASSWORD>"}'

curl -sX POST localhost:8000/chat/default/messages -b jar.txt \
     -H 'content-type: application/json' \
     -d '{"content":"Explain FastAPI routing in two sentences."}'

curl -N -X POST 'localhost:8000/chat/researcher/messages?stream=true' -b jar.txt \
     -H 'content-type: application/json' -d '{"content":"What time is it in Tokyo?"}'
```

FastAPI works out where each argument comes from by its type and name: `agent` matches a name in
the path, so it is a **path parameter**; `body` is a Pydantic model, so it is the **request
body**; `stream` matches neither, so it is an optional **query parameter**.
`Annotated[..., Path(...)]` and `Annotated[..., Query(...)]` add the titles and descriptions
that show up in `/docs`.

With `?stream=true` the reply leaves as server-sent events instead of one JSON body — each
chunk JSON-encoded, because model output contains newlines and raw text would break the
`data: ...\n\n` framing:

```
data: {"delta": "It is "}
data: {"delta": "18 degrees\nin "}
data: {"delta": "Berlin."}
data: [DONE]
```

## Layout

| Path                       | Layer                                                      |
| -------------------------- | ---------------------------------------------------------- |
| `app/main.py`              | The app object; `include_router`                           |
| `app/routers/chat.py`      | Routing — path, method, the function that handles it        |
| `app/routers/auth.py`      | Login, logout, who-am-I                                     |
| `app/security.py`          | The session cookie and the `CurrentUser` dependency         |
| `app/app_models.py`        | API shapes — the contract with the frontend                 |
| `app/agent/agent_models.py`| Agent shapes — `ChatMessage`, `AgentResult`, `AgentConfig`, `AgentName` |
| `app/agent/loop.py`        | The loop: call the model, run tools, return a reply         |
| `app/agent/tools.py`       | Tool schemas + the functions behind them, in one registry   |
| `app/agent/config.py`      | The agent registry — the values filled into `AgentConfig`   |
| `app/agent/prompts/*.txt`  | The instructions themselves                                 |
| `app/config.py`            | App settings — secrets and endpoints, from the environment  |

## Auth

`POST /auth/login` checks the credentials and calls `response.set_cookie(...)`; the browser sends
that cookie back on every later request, and `GET /auth/me` reads it back. The cookie is set
`HttpOnly` (JavaScript cannot read it, so XSS cannot steal it), `Secure` (https only — turn it off
locally with `COOKIE_SECURE=false`), and `SameSite=Lax`, which is what stops another site from
POSTing to this API with your cookie attached.

It carries a **signed username**, not a random session id — `itsdangerous` signs it with
`SESSION_SECRET`, so the server can trust it without storing anything. Tampering fails the
signature, and `max_age` expires it. The tradeoff: there is no server-side logout, since a
stolen cookie stays valid until it expires. A session table fixes that, and is the natural next
step once there is a database.

Endpoints take the user through a dependency:

```python
async def send_message(..., user: CurrentUser) -> SendMessageResponse:
```

`CurrentUser` is `Annotated[User, Depends(get_current_user)]`. No cookie, a forged cookie, or an
expired one all 401 before the endpoint body runs — and the endpoint is handed a `User` rather
than a cookie, which is exactly where the *next* check belongs: does this conversation belong to
this user?

`AUTH_USERNAME` / `AUTH_PASSWORD` stand in for a users table — one account, from the environment,
compared with `secrets.compare_digest` so the comparison is constant-time. Replace `authenticate()`
with a real lookup plus a password hash (`argon2`, `bcrypt`) and nothing else in this layer moves.

## Two kinds of model, two kinds of configuration

- **API models** ([`app/app_models.py`](app/app_models.py)) — `SendMessageRequest` /
  `SendMessageResponse`. Public: changing a field breaks the frontend, so it changes slowly.
- **Agent models** ([`app/agent/agent_models.py`](app/agent/agent_models.py)) — `ChatMessage`,
  `AgentResult`, and the `AgentConfig` / `AgentName` types. Internal: the loop counts `steps` and
  records `tools_called`, which the API does not expose today. The router does the mapping, so
  the agent can grow new fields without reshaping the response, and the two never drift into one
  accidental shape.

`agent_models.py` holds the *shapes*, `agent/config.py` holds the *values* poured into them —
so a new agent is an entry in `AGENTS` plus a name in `AgentName`, and changing what an agent
*can* be configured with is a separate edit in a separate file.


- **App settings** ([`app/config.py`](app/config.py)) — deployment wiring: the API key, the
  base URL. Differs per environment, contains secrets, comes from `.env`, never committed.
- **Agent settings** ([`app/agent/config.py`](app/agent/config.py)) — behaviour: model,
  temperature, instructions, tools. Same in every environment, committed and reviewed like
  code, and a registry rather than one global, because a service usually runs several agents.

Three are defined, differing in model, prompt, sampling and tool set:

| agent        | model                                | temp | tools                                    |
| ------------ | ------------------------------------ | ---- | ---------------------------------------- |
| `default`    | `meta-llama/Llama-3.3-70B-Instruct`  | 0.6  | `get_weather`, `current_time`            |
| `coder`      | `Qwen/Qwen3-235B-A22B-Instruct-2507` | 0.2  | `search_docs`                            |
| `researcher` | `Qwen/Qwen3-Next-80B-A3B-Thinking`   | 0.3  | `search_docs`, `get_weather`, `current_time` |

Tools are listed by name, not by function: the config stays plain data, and the loop resolves
names against `tool_registry` per request, so an agent only ever sees the schemas it is allowed
to call. A name that is not in the registry fails at import, not at the first model call.

The caller picks an agent in the path — `/chat/coder/messages`. `AgentName` is a `StrEnum`, so
`/docs` renders it as a dropdown and an unknown name is a 422 before your code runs.

## Expanding it

- **A new agent** — add a name to `AgentName`, an entry to `AGENTS`, a `.txt` file to `prompts/`.
- **A new tool** — one decorated function in `app/agent/tools.py`, then list its name in the
  `tools` of whichever agents should have it. The loop already handles the round trip.
- **History** — a store module and a `conversation_id` in the path, so the agent
  gets prior messages instead of only the new one.
- **Security, uploads, streaming** — later layers, each a new router or dependency.
