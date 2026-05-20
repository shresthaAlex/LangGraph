## LLMs Don’t Have Memory 

LLMs Don’t Have Memory — So how memory works in GenAI systems and why it is essential for building chatbots and AI agents.


## LLMs at Inference: Stateless Parameterized Math Functions

Large Language Models (**LLMs**) during inference act as **parameterized math functions**, represented mathematically as y=fθ(x), where the output depends solely on the current input and fixed parameters learned during training.

-   **Parameterized function breakdown**: In mathematics, a parameterized function's output relies on both input and additional parameters (e.g., y=ax requires both x (user-provided) and a (fixed)). 
- This mirrors **linear regression**, where data training yields parameters m (slope) and b (intercept) for the best-fit line y=mx+b, rewritten as y=fm,b(x)—parameters come from training data, not inference input.
    

> **💡 Key Insight:** Changing x (prompt) alters y, but θ remains fixed, explaining why different prompts yield different outputs.

## Stateless Nature of LLMs: No Intrinsic Memory

LLMs are **stateless** by design: output depends _only_ on current input, not prior history—"A system is stateless if its output depends only on the current input and not on anything that has happened before."

-   **Mechanism demonstration**: First call: y1=fθ(x1) (e.g., prompt "My name is Alex " → greeting). Second call: y2=fθ(x2) (e.g., "What is my name?" → "I don't know"), ignoring x1 and y1​.
    
-   **Code example** :
    
  
    
    ```python
    # First invocation (x1)
    llm.invoke("My name is Alex.")  # y1: "Nice to meet you, Alex."
    
    # Second invocation (x2, independent)
    llm.invoke("What is my name?")    # y2: "I'm sorry, I do not know your name."
    ```
    
-   **Implication**: LLMs lack intrinsic memory—past conversations are forgotten each call, creating a "deadlock" since GenAI apps (chatbots, agents) require memory for functionality.
    

> **⚠️ Warning:** Statelessness means every inference call is independent; no automatic retention of context, unlike human memory.

## Enabling Concepts for External Memory: Context Window and In-Context Learning

To build memory externally, leverage two foundational abilities.

-   **Context window**: Maximum tokens an LLM can process/read/remember at once before responding (e.g., modern LLMs: 128k+ tokens ≈ 200 PDF pages; Gemini: 1M tokens). Analogy: Camera lens size—larger lens captures more scene.
    
    -   **Connection**: Allows stuffing large x (e.g., full history), critical for memory hacks since x has no hard limit beyond this.
        

**In-context learning** (emergent ability in large LLMs): LLM uses prompt-embedded info/patterns _in addition to_ parametric knowledge to answer (e.g., upload unseen 100-page PDF + question → LLM reads/answers from it).

-   **Why it matters**: Parametric knowledge (from θθ) insufficient for novel/user-specific data; prompt provides ad-hoc "learning."
    

These enable memory: Large context window holds history; in-context learning lets LLM use it.

## Short-Term Memory: Conversation Buffer via History Concatenation

**Short-term memory (STM)** simulates memory by concatenating full conversation history into every prompt, turning stateless LLM stateful via a **messages list** (conversation buffer).

-   **Mechanism** (step-by-step):
    
    1.  First user message x1​ → y1=fθ(x1), append y1 to messages.
        
-   Next x2x2​ → prompt = concat(x1,y1,x2​) → y2=fθ(concat), LLM uses history via in-context learning.
    
-   **Code implementation**:
    

    
    ```python
    messages = []  # Conversation buffer (state)
    messages.append({"role": "user", "content": "My name is Alex."})  # x1
    y1 = llm.invoke(messages)  # "Nice to meet you..."
    messages.append({"role": "assistant", "content": y1})  # Append y1
    
    messages.append({"role": "user", "content": "What is my name?"})  # x2
    y2 = llm.invoke(messages)  # "Your name is Alex."
    ```
    
-   **Scope**: **Conversation/thread-scoped**—one buffer per session/thread (e.g., ChatGPT chats). New conversation resets buffer for coherence.
    
-   **Significance**: Provides continuity within a thread using context window + in-context learning; temporary (lost on restart).
    

## STM Feature



**Stateful hack**

Messages list holds history, making system stateful.

**Persistence fix**

Store/retrieve via DB with thread IDs (e.g., load thread-1 messages on switch).

## Problems with Short-Term Memory

STM works short-term but fails at scale.

-   **Fragility**: Lost on restarts/crashes/new chats unless persisted to DB (use thread IDs to save/load).
    
-   **Context window overflow**: Long conversations exceed token limit → incoherent/hallucinated responses. Solution: **Trimming** (send recent N messages) + **summarization** (LLM summarizes old history, prepend to recent).
    
-   **Thread-scoped limitations** (no cross-conversation continuity):
    
    1.  No user preferences persist (e.g., "Prefer Python" forgotten in new thread).
        
-   Learning doesn't compound (e.g., optimized SQL reverts).
    
-   Cross-thread reasoning impossible (e.g., "What did we discuss yesterday?").
    
-   **Bigger picture**: Blocks personalization/personal assistants needing multi-thread facts.
    

> **⚠️ Common Misconception:** STM seems permanent but is conversation-bound; switching threads erases context without persistence.

## Long-Term Memory: Cross-Conversation Persistence

**Long-term memory (LTM)** stores selective, durable info surviving conversations/threads—**user-level/system-level facts, strategies** useful for days/months (e.g., "User prefers Python," book-writing context).

-   **Key properties** (building on STM limits):
    
    -   **Durable/selective**: Identifies/extracts stable, reusable info (ignores noise).
        
-   **Cross-scoped**: Exists beyond single threads for personalization/compounding.
    

**Why needed**: Enables user prefs (e.g., gender/nationality/role), behaviors (what works/fails), decisions/workflows.

## Types of Long-Term Memory

LTM stores three types, each serving distinct recall needs:



**Episodic**

Past events/outcomes

"Last deployment credentials failed"; "Solution X rejected."

Answers "What happened before?" improving current decisions.

**Semantic** (most common)

Facts about user/system/task

"User prefers Python"; "Uses PostgreSQL"; "Budget ₹10k."

Personalizes/systematizes (user/system-level truths).

**Procedural**

How-tos/strategies/behaviors

"Avoid subqueries, use window functions"; "If tool X fails, try Y"; "Step-by-step explanations."

Compounds learning; feels adaptive over time.

## Long-Term Memory Workflow: Four Core Steps

LTM operates in a cycle around conversations (framework-agnostic high-level view).

1.  **Creation/Update**: During chat, scan user/model/tool outputs for **memory candidates** (e.g., "I prefer Python").
    
    -   Steps: Extract → filter noise → tag scope (user/app/agent) → decide (new/update/ignore).
        
2.  **Storage**: Save processed memory durably (e.g., relational DB, key-value, vector DB for semantic search) + metadata/IDs for retrieval. Survives restarts.
    
3.  **Retrieval**: In new chat, check current input → selective search (not exhaustive) → pull relevant subset. Focus: "What to remember now?"
    
4.  **Injection**: Retrieved memories → short-term buffer/prompt (becomes tokens for LLM via context window). _Never_ direct LLM-memory interaction.
    

> **🔗 Connection:** LTM augments STM—retrieval injects into buffer for in-context use, solving cross-thread issues.

## Challenges in Building Long-Term Memory Systems

Implementing LTM adds complexity atop agents/chatbots.

-   **Memory creation**: Deciding what to extract (noise vs. enduring info) during real-time chat.
    
-   **Real-time retrieval**: From vast store, select _relevant_ pieces for current context.
    
-   **Orchestration**: Integrating stores, handling moving parts (DBs, searches) in complex agentic systems.
    

----------

## Challenges and Solutions for Long-Term Memory in LLMs

Implementing **long-term memory** (persistent storage and retrieval of information beyond a single interaction) in applications using **LLMs** (**large language models**) can be tricky, as these models lack built-in mechanisms for it.

-   **Managed solutions emerge to simplify this:** Recent libraries and platforms act as a **memory layer** for **GenAI** (**generative AI**) apps and **agentic AI** (**autonomous AI agents** that make decisions and take actions). These handle the full lifecycle—creating, storing, and retrieving memories at the right time—allowing developers to focus solely on building the core application by simply calling their functions.
    
-   **Why this matters:** This abstraction reduces complexity, enabling scalable AI apps that "remember" user history or context across sessions, which is essential for real-world deployment.
    

## Key Libraries and Platforms

Several popular tools have gained traction, integrating seamlessly with frameworks like **LangGraph** (a graph-based workflow tool for AI agents from the LangChain ecosystem).

**LangMem**

From the LangChain family.

Easy integration with LangGraph for building AI agents; manages end-to-end memory operations.

**MemZero**

Recently popular platform.

Provides a dedicated memory layer for GenAI apps, handling storage and retrieval automatically.

**SuperMemory**

Manages long-term memory specifically for GenAI applications.

##

> Think of these like cloud services for memory—you plug them in like AWS for storage, without managing servers yourself.
    

> **💡 Key Insight:** By offloading memory management, developers can prototype agentic apps faster, as memory is no longer a bottleneck.  

## Root Causes and Ongoing Research

-   **Fundamental limitation:** All these challenges arise because LLMs have no **intrinsic memory** (built-in, default capability to retain information persistently within the model itself).
    
-   **Research direction:** Efforts are underway to engineer LLMs with native memory, reducing reliance on external systems.
    
    -   **Example:** Google's research paper "Titans + Mirage" proposes a novel **transformer architecture** (the core neural network design behind most LLMs) infused with intrinsic memory mechanisms.
        

**Building on the problem:** This research directly addresses the need for memory in GenAI and agentic apps, where without it, persistent context or learning from interactions is impossible—making external memory layers a temporary bridge.

> **ℹ️ Note:** The field is evolving quickly because memory is non-negotiable for advanced AI applications like autonomous agents that adapt over time.  

