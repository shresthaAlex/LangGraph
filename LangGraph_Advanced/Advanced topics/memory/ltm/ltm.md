## Understanding Long Term Memory in LangGraph

Long-term memory in LangGraph is essential for creating a more interactive and personalized user experience in chatbots. The concept revolves around the ability to store and retrieve user-specific information over time, allowing the chatbot to remember details about the user and provide tailored responses.

### Creating New Memories

The workflow for creating new memories starts with a "start" node, which leads to a "remember" node, and finally to an "end" node. This workflow is connected to a memory store that initially has no existing memories. The primary purpose of this workflow is to create new memories while chatting, rather than using existing ones .

### Memory Extraction Process

To facilitate memory creation, a Large Language Model (LLM) is utilized. When a user sends a message, this model determines whether the message contains information worth remembering. If the message includes relevant details, it extracts this information and stores it in the memory store . The model is referred to as an "extractor LLM," as its main function is to extract memories .

### Structuring the Memory Decision

The memory decision process involves creating a structured output that informs the LLM whether to remember a piece of information. This structured output includes a boolean variable indicating if the information is new or already exists. If the information is new, it is stored in a list of strings, which allows for multiple memories to be captured from a single user message .

### Workflow Integration

The integration of this memory functionality into a chatbot allows for personalized responses. The chatbot first checks the memory store for existing user information before responding, making the interaction more contextual and relevant .

### Persistent Memory Storage

The initial implementation of memory storage uses a volatile memory store, meaning that information is lost when the program is restarted. To solve this issue, a persistent memory store, such as PostgreSQL, is introduced. This ensures that user memories are retained even after the system is shut down .

### Implementation Steps

1.  **Setting Up PostgreSQL**: Users must install PostgreSQL on their machines, typically using Docker. This setup allows for a robust and persistent memory store that can be utilized in production-grade systems .
2.  **Creating Memory Stores**: The code involves creating memory stores that can handle both existing and new memories. The memory store is structured to allow for easy retrieval and storage of user information .
3.  **Semantic Search Capability**: To enhance the memory retrieval process, semantic search is implemented. This allows the system to search for memories based on the meaning of the current conversation rather than exact matches, improving the relevance of retrieved memories .
4.  **Testing Memory Persistence**: After implementing the persistent memory store, testing is conducted to ensure that memories remain intact after system restarts. This confirms that the new setup effectively retains user information .

### Conclusion

In summary, the implementation of long-term memory in LangGraph significantly enhances the capabilities of chatbots, allowing them to create, store, and retrieve user-specific information effectively. By integrating persistent memory storage and semantic search, developers can build more intelligent and responsive systems that improve user interaction .
