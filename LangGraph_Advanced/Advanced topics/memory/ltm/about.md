
## **Long-Term Memory in LangGraph**.

Building **AI chatbots with long-term memory** using [LangGraph](https://www.langchain.com/langgraph).

The idea is:

-   Users talk across many chat threads.
-   Important information about the user gets scattered across conversations.
-   The chatbot extracts useful user information and stores it permanently.
-   Later, the chatbot retrieves those memories to give personalized responses.

----------

# Short-Term vs Long-Term Memory

## Short-Term Memory

-   Exists only during the current conversation/thread.
-   Usually stored in the LLM context window.
-   Lost when the conversation ends.

Example:

-   “Explain transformers”
-   Follow-up messages inside same chat.

----------

## Long-Term Memory

-   Persistent across sessions and threads.
-   Stored in databases or memory stores.
-   Used for personalization.

Example memories:

-   User likes Python
-   User prefers concise answers


This allows responses like:

> “Sure Alex, here’s a Python example…”

instead of generic answers.

----------

# Memory Store in LangGraph

LangGraph implements long-term memory using **stores**.

Main abstraction:

-   `BaseStore` → abstract class

Important implementations:

1.  `InMemoryStore`
    -   Stores data in RAM
    -   Temporary
    -   Good for learning/testing
2.  `PostgresStore`
    -   Stores data in PostgreSQL
    -   Persistent
    -   Production-ready
3.  `RedisStore`
    -   Redis-based persistence
    -   Production-grade

----------

# Important Store Operations

## Create memory → `put()`

```python
store.put(namespace, key, value)
```

Example:

```python
store.put(
    ("users", "u1"),
    "1",
    {"memory": "User likes pizza"}
)
```

----------

## Fetch one memory → `get()`

```python
store.get(namespace, key)
```

----------

## Fetch all memories → `search()`

```python
store.search(namespace)
```

----------

# Namespace Concept

Namespaces organize memories like folders.

Example:

```python
("users", "u1")
```

Meaning:

```
users/
   u1/
```

Another namespace:

```python
("users", "u1", "preferences")
```
Stores:
-   prefers dark mode
-   likes Python

----------

# Semantic Search in Memory

Normal search:

-   fetches all memories

Semantic search:

-   fetches only relevant memories

Example query:

```python
"What is the user learning?"
```

Returns:

-   “User is learning machine learning”

----------

# How Semantic Search Works

The store uses embeddings.

Example:

```python
embedding_model = OpenAIEmbeddings(
    model="text-embedding-3-small"
)

store = InMemoryStore(
    index={
        "embed": embedding_model,
        "dims": 1536
    }
)
```

Then:

```python
store.search(
    namespace,
    query="What are the user's preferences?",
    limit=3
)
```

----------

# Long-Term Memory Chatbot Flow

The chatbot workflow:

```
User Message
      ↓
Read Relevant Memories
      ↓
Inject into Prompt
      ↓
LLM Generates Personalized Reply
```

----------

# Example Personalization

Stored memory:

```
User likes Python
```

User asks:

```
Write Fibonacci code
```

Response automatically becomes Python-based.

----------

# Creating New Memories Automatically

The system also learns from users.

Workflow:

```
User Message
      ↓
LLM checks:
"Is there something worth remembering?"
      ↓
If yes → store memory
```

Example:

User says:

```
"My favorite language is Python"
```

Stored as:

```
User prefers Python
```

----------

# Structured Output with Pydantic

The video uses [Pydantic](https://docs.pydantic.dev) to force clean LLM outputs.

Example:

```python
class MemoryDecision(BaseModel):
    should_write: bool
    memories: list[str]
```

The LLM must return:

```json
{
  "should_write": true,
  "memories": [
    "User likes Python"
  ]
}
```

----------

# Duplicate Memory Problem

Problem:  
Repeated messages create duplicate memories.

Example:

-   “My name is Alex”
-   repeated multiple times

Solution:

-   Send existing memories to the LLM
-   Ask whether extracted memory is new or already stored

Memory item structure:

```python
class MemoryItem(BaseModel):
    text: str
    is_new: bool
```

Only store if:

```python
is_new == True
```

----------

# Final Production Workflow

Final LangGraph workflow:

```
START
   ↓
Remember Node
   ↓
Chat Node
   ↓
END
```

## Remember Node

-   extracts memories
-   stores them

## Chat Node

-   retrieves memories
-   personalizes responses

----------

# Why InMemoryStore Is Not Enough

`InMemoryStore` uses RAM.

Problem:

-   restart app
-   all memories disappear

So production systems use:

-   PostgreSQL
-   Redis

----------

# PostgreSQL Setup

-  runs PostgreSQL using [Docker Desktop](https://www.docker.com/products/docker-desktop).

Command :

```
docker run ...
```

Then LangGraph uses `PostgresStore` instead of `InMemoryStore`.

Result:

-   memories survive restarts
-   persistent chatbot memory

----------

# Core Production Architecture

A production-grade memory chatbot typically has:

```
Frontend Chat UI
       ↓
LangGraph Workflow
       ↓
Memory Extraction LLM
       ↓
Persistent Store (Postgres/Redis)
       ↓
Semantic Retrieval
       ↓
Personalized Responses
```

----------

# Most Important Concepts

1.  Long-term memory = persistent user knowledge
2.  Namespace = folder-like organization
3.  `put`, `get`, `search` are core APIs
4.  Semantic search retrieves relevant memories
5.  LLMs can both:
    -   read memories
    -   create memories
6.  Deduplication is necessary
7.  Production systems use Postgres/Redis, not RAM

This is one of the foundational architectures behind modern AI assistants and personalized chatbot systems.