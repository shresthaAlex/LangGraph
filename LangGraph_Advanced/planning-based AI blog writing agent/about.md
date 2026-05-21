
## **Planning-based AI blog writing agent** 

Building a **planning-based AI blog writing agent** using LangGraph, LLMs, internet research, and image generation.

## Main Idea: Planning Agent

A **planning agent** is different from a normal AI workflow because it:

1.  **Creates a plan first**
2.  Then executes tasks step by step

Instead of directly generating output, the system:

-   Breaks a task into subtasks
-   Assigns subtasks to workers
-   Combines results into a final output



----------

# **Blog-Writing AI Agent** Features

-   Generate technical blogs
-   Plan blog sections automatically
-   Perform internet research when needed
-   Generate citations
-   Add AI-generated images
-   Show logs/evidence
-   Provide GUI using Streamlit

----------

# Architecture Overview

## Workflow

```
Topic
  ↓
Router
  ↓
Research (optional)
  ↓
Planner / Orchestrator
  ↓
Worker Nodes (parallel)
  ↓
Reducer
  ↓
Final Blog
```

----------

# 1. Router Node

The router decides:

-   Does this topic need internet research?
-   What kind of topic is it?
Three modes:

| Mode | Meaning |
|---|---|
| Closed Book | LLM already knows enough |
| Hybrid | Some research needed |
| Open Book | Heavy internet research required |

## Examples

| Topic | Mode |
|---|---|
| Self-attention | Closed book |
| Open-source LLMs | Hybrid |
| Latest AI news | Open book |
The router also generates **search queries** if research is needed.

----------

# 2. Research Node

Uses:

-   Tavily search API

Purpose:

-   Perform web searches
-   Gather evidence
-   Store structured research data

The transcript defines:

## Evidence Item

Contains:

-   title
-   URL
-   publication date
-   source
-   snippet

Multiple evidence items become an:

## Evidence Pack

Used later by planner and workers.

----------

# 3. Planner / Orchestrator

The planner creates a structured blog plan.

Uses:

-   Pydantic schemas
-   Structured outputs

----------

## Plan Object

Contains:

-   Blog title
-   Audience
-   Tone
-   Tasks (sections)

----------

## Task Object

Each section contains:

-   ID
-   Title
-   Goal
-   Bullets/subtopics
-   Target words
-   Tags
-   Research requirements
-   Citation requirements
-   Code requirements

----------

# 4. Fan-Out Mechanism

The system dynamically creates worker nodes.

Example:

If planner creates:

-   5 sections → 5 workers
-   9 sections → 9 workers

This is implemented using:

-   LangGraph `Send()` API

Each worker receives:

-   Topic
-   Task description
-   Overall plan
-   Research evidence

----------

# 5. Worker Nodes

Each worker:

-   Writes one blog section
-   Works independently
-   Runs in parallel

Prompt includes:

-   Blog title
-   Topic
-   Section goal
-   Required subpoints
-   Research evidence

Output:

-   Markdown section

----------

# 6. Reducer Node

Combines all sections into one final blog.

Initially:

-   Simply stitched markdown together

Later upgraded into a **subgraph**.

----------

# Image Generation System

Reducer evolved into 3-step process.

----------

## Step 1: Merge Content

Combine all worker outputs into full markdown.

----------

## Step 2: Decide Images

LLM analyzes blog and determines:

-   Where images should go
-   What type of images are needed

Creates:

-   placeholders
-   image prompts

----------

## Global Image Plan

Contains:

### Markdown with placeholders

Example:

```
[IMAGE_PLACEHOLDER_1]
```

### Image Specs

Each image spec contains:

-   filename
-   prompt
-   quality
-   size

----------

## Step 3: Generate Images

Uses:

-  Gemini API

Workflow:

1.  Send prompts to Gemini
2.  Generate images
3.  Save images locally
4.  Replace placeholders with file paths

Final markdown now contains:

-   text
-   images

----------

# GUI Layer

Frontend built using:

-   Streamlit

Capabilities:

-   Topic input
-   Live progress updates
-   Generated blog view
-   Evidence tab
-   Logs tab
-   Images tab
-   Blog history

----------

# Technologies Used


| Technology | Purpose |
|---|---|
| LangGraph | Multi-agent orchestration |
| LangChain | LLM tooling |
| Streamlit | GUI |
| OpenAI GPT-4.1-mini | Text generation |
| Google Gemini | Image generation |
| Tavily | Web research |
| Pydantic | Structured schemas |
----------

# Key Concepts 

## Orchestrator-Worker Pattern

Planner creates tasks → workers execute in parallel.

----------

## Fan-Out Pattern

Dynamic worker creation based on number of sections.

----------

## Reducer Pattern

Merge outputs from parallel workers.

----------

## Structured Output

Using Pydantic models to force predictable LLM outputs.

----------

# Stages of Development

## Stage 1

Basic blog generation

Features:

-   planner
-   workers
-   reducer

No:

-   research
-   images

----------

## Stage 2

Add internet research

Features:

-   router
-   Tavily search
-   evidence packs

----------

## Stage 3

Add image generation

Features:

-   placeholders
-   image planning
-   Gemini image generation

----------

## Stage 4

GUI with Streamlit

----------

# Overall Goal

The project demonstrates how to build a realistic multi-agent AI application that:

-   plans before acting,
-   researches dynamically,
-   executes subtasks in parallel,
-   and produces rich outputs (blogs + images + citations).

