# progress upto now
AFter covering the difference between Agentic AI and Generative AI, the difference between LangGraph and LangChain, and core LangGraph concepts and  various LangGraph workflows (parallel, sequential, conditional, iterative) 
and progressively building and enhancing a chatbot .
Chatbot enhancements included adding UI, streaming, resume chat functionality, database integration, observability (LangSmith), and external tools (Stock Market, Web Search, Calculator) .

Now integrating the Model Context Protocol (MCP) into the existing chatbot .

# Understanding Model Context Protocol (MCP)
- MCP is defined as an improved and standardized way to integrate tools with an LLM application or chatbot, addressing inherent flaws in the traditional tool technique .

- The traditional approach requires developers to write custom code for user-defined tools (e.g., GitHub integration) when built-in tools are unavailable .
- For complex services like GitHub, multiple separate tools must be written for different tasks (e.g., one for pull requests, another for commits, etc.)  .

## The Brittleness Problem with Traditional Tools
- The traditional tool approach is brittle because the client-side tool code is tightly coupled to the server-side API (e.g., GitHub's API)  .
- If the external API service (the server) updates its API (e.g., changing URLs or attribute names like title to title_name), the chatbot's tool code (the client side) immediately breaks and throws an error .
- This forces the developer to manually study the new documentation and update the client-side code for every broken tool  .
- This maintenance issue scales rapidly: if a company has $n$ tools and $m$ separate chatbots, the problem becomes an 
n×m maintenance headache, requiring constant upkeep instead of focusing on new features  .

Here is a visualization of the failure mechanism in the traditional tool approach:

![Brittleness of the Traditional Tool Approach](/LangGraph_Advanced/Advanced%20topics/with%20mcp/images/Brittleness%20of%20the%20Traditional%20Tool%20Approach.png)


# Code Transition: Sync Tool to Async MCP Client
![Code Transition: Sync Tool to Async MCP Client](/LangGraph_Advanced/Advanced%20topics/with%20mcp/images/Code%20Transition_%20Sync%20Tool%20to%20Async%20MCP%20Client.png)


# MCP Client Development
- The MCP client is built using the MultiServerMCPClient class from the langchain_mcp_adapters library .

- The client connects using a configuration that specifies the server name, the transport type, and the command/URL .
- For a local server (running on the same machine), the transport used is STDIO (Standard Input Output)  .

- For a remote server (deployed on a separate machine), the transport used is Streamable HTTP .

- The function await client.get_tools() dynamically fetches the list of available tools (and their definitions) from the connected MCP server(s) .

- The Multi-Server capability allows a single client to connect to multiple MCP servers simultaneously (e.g., a math calculation server and an expense tracking server) ... .
- The chatbot can use these dynamically fetched tools for tasks like calculations or expense tracking without having any of the corresponding tool code written on the client side .

# Final Integration and Future Plans
The final integrated code can utilize a mixture of traditional tools (like Get Stock Price) and MCP clients (for Math and Expense Tracking) .

Production Challenge: The integration of the asynchronous MCP client with the Streamlit front end is complicated because Streamlit is fundamentally a synchronous library  .

To manage this, asynchronous counterparts were required for other libraries, such as using AIOSQLite instead of SQLite for the database  .

For a robust production setup,  expose the back end using an asynchronous framework like FastAPI and use a naturally asynchronous front end like React or Next.js, as the current Streamlit approach is considered "hacky"  .

The next is adding Retrieval-Augmented Generation (RAG) capability to the chatbot, enabling it to answer questions based on internal documents .



