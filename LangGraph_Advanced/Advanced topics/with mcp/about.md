# Integration of MCP (Model Context Protocol) 

## MCP 

- The MCP is an enhanced method for integrating tools within chatbots and LLM applications, addressing flaws present in traditional tool integration techniques. 
- By utilizing MCP, developers can standardize the connection of tools to their applications, reducing maintenance issues caused by changes in tool APIs. 

# MCP Benefits
- MCP addresses the maintenance problem by ensuring a clear separation of concerns between the client and server sides, allowing the client to interact with the server using a simple configuration code. 
   - This setup means that any changes on the server side, such as API updates, do not require modifications to the client code. 
   
- Overall, MCP streamlines the development process and reduces the need for extensive coding, making it easier for users to access and utilize tools without worrying about frequent updates.

# MCP Client Development
- Creating an MCP client in LangGraph to facilitate communication with an MCP server, without delving into server creation, as LangGraph does not support this. 
- It emphasizes that users will connect their custom-built MCP client to an existing server setup, primarily using previously written code for a chatbot with tools. 
- illustrate how to implement an MCP client, highlighting the ease of integration and the absence of required changes on the client side when modifications occur on the server.

## Asynchronous Code Conversion
To build the MCP client, the first step involves converting synchronous code into asynchronous code since the library used for the MCP client only operates in asynchronous mode.
   -  The process begins with copying the existing synchronous code of chatbot with tools into a new file and then systematically modifying it to handle asynchronous execution. This conversion enables the execution of multiple tasks in parallel, ultimately speeding up the overall process.

# MCP Server Overview
- The MCP server is developed using the MCP library, and 

Next,  write a client code to connect to the server,  utilizing the LangChain MCP adapters library to create an MCP client that can perform by connecting to the server. 
The code will allow us to retrieve and display the available tools on the server.

# MCP Client Implementation
- creation of an MCP client using LangGraph and the LangChain library, i connect to a remote MCP server named Expense Tracker. By adding simple configurations, one can effortlessly track expenses through commands without writing extensive code. The session emphasizes the power of using MCP over traditional tools, highlighting its future-proof and robust nature.

# Final
The chat bot now includes a new functionality supporting MCP and will soon add a capability for answering questions based on internal documents. 