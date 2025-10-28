# Medical Agent - Minimal Setup

## 📁 Modular Structure (Like Inngest)

```
backend/app/
├── agent/                    # Agent module (like inngest/)
│   ├── __init__.py          # Exports medical_agent
│   ├── state.py             # State definition
│   ├── graph.py             # Graph definition
│   └── nodes/               # Agent nodes (like functions/)
│       ├── __init__.py
│       └── respond.py       # Hello world node
│
├── api/
│   └── chat.py              # API endpoint (like users.py)
│
└── main.py                  # Register agent (like Inngest)
```

## 🎯 How It Works

### 1. State (`state.py`)
Defines what data flows through the agent.

```python
class AgentState(TypedDict):
    message: str      # Input
    response: str     # Output
```

### 2. Nodes (`nodes/respond.py`)
Individual processing steps - like Inngest functions.

```python
def generate_response(state):
    state["response"] = f"Hello! You said: {state['message']}"
    return state
```

### 3. Graph (`graph.py`)
Connects nodes together - defines the flow.

```python
workflow.add_node("respond", generate_response)
workflow.set_entry_point("respond")
```

### 4. API (`api/chat.py`)
Endpoint that invokes the agent.

```python
result = medical_agent.invoke({"message": "hello"})
return result["response"]
```

## 🚀 Test It

### Backend
```bash
cd backend
INNGEST_DEV=1 uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm run dev
```

Open: http://localhost:5173

Type: `"Hello world"`  
Get: `"Hello! You said: 'Hello world'. Agent is working! 🎉"`

## 🔧 How to Extend

### Add a new node:

1. Create `nodes/new_node.py`:
```python
def my_node(state):
    # Do something
    state["new_field"] = "value"
    return state
```

2. Add to `graph.py`:
```python
from app.agent.nodes.new_node import my_node

workflow.add_node("my_node", my_node)
workflow.add_edge("my_node", "respond")
```

3. Update `state.py` if needed:
```python
class AgentState(TypedDict):
    message: str
    response: str
    new_field: str  # Add new field
```

## 📚 Compare with Inngest Pattern

| Inngest | Agent |
|---------|-------|
| `inngest/functions/` | `agent/nodes/` |
| `example.py` function | `respond.py` node |
| `ALL_FUNCTIONS` list | Graph connects nodes |
| Triggered by events | Triggered by API call |
| Background jobs | Synchronous flow |

Both are **modular** - easy to add new functions/nodes!
