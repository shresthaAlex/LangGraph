# Evolution of the Multi-Utility Chatbot
- The existing project is an agentic AI chatbot built using LangGraph, which has incrementally added features like UI, streaming, persistence (resume chat), observability, tool integration, and the MCP concept .

- NOW converting into a RAG chatbot by integrating Retrieval Augmented Generation (RAG), giving it the power to answer questions based on uploaded documents  .

> Treating RAG as another tool simplifies the integration into complex agentic AI applications s .


- This integration transforms the application into a Multi-Utility Chatbot capable of normal conversation, using past tools (e.g., stock price), and chatting about personal documents or uploaded files like PDFs ... .

- The RAG functionality allows users to upload a document (e.g., a PDF blog) and ask questions based only on the content of that uploaded file ... .


# RAG: Why, What, and How


**Why RAG is Necessary**
- RAG primarily addresses three major limitations of large language models (LLMs) .

## Problem Area | Description | RAG Solution/Benefit

| **Problem Area**    | **Description**                                                                                                                                 | **RAG Solution/Benefit**                                                                                                                                                      |
|---------------------|-------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Outdated Knowledge** | LLMs have a fixed knowledge cutoff (training completion date), so they can't provide answers about events or developments after that time.    | **Solution:** RAG allows systems like ChatGPT to perform live web searches, retrieving current, up-to-date information. This ensures the model has access to recent data and can answer questions based on the most current sources. |
| **Privacy**           | LLMs cannot access or answer questions about private data (e.g., company financial reports, personal expense sheets) since this data was not included in their training. | **Solution:** RAG can be integrated with private document storage, allowing LLMs to answer queries over protected data. By connecting the model to secure, internal datasets, it can generate responses based on sensitive or proprietary information without violating privacy. |
| **Hallucination**     | LLMs sometimes generate false or misleading information (e.g., creating non-existent citations, links, or facts) with confidence.            | **Solution:** By grounding LLM responses to trusted, verified context (using RAG to pull relevant, fact-checked information), hallucinations are minimized. The model can only answer based on the available, confirmed data, ensuring more reliable and accurate outputs. |

# What RAG Is (The Core Principle)
- RAG operates on the simple principle of In-Context Learning  .

**In-Context Learning:**
-  If you provide an LLM with additional context during a chat, the LLM can use that context to answer questions  .

- When dealing with private data, the solution is to add the document's content directly to the prompt as context, enabling the LLM to answer the query based on the combined information ... .

> ❗ Important: Simply pasting the entire document content into the prompt is often impossible because the LLM's context window is limited (handles a certain number of tokens) ... .

- **RAG's crucial step is Context Filtering**: instead of pasting the entire document, RAG only pastes the specific part of the context that is relevant to the user's query to avoid exceeding the context window limit ... .

# How RAG Works (Architectural Flow)
- RAG uses a multi-step process to filter and augment the LLM's input  .

![RAG High-Level Architecture](/LangGraph_Advanced/Advanced%20topics/with%20rag/images/RAG%20High-Level%20Architecture.png)



- **Splitting:** The document is divided into smaller chunks or splits s .

- **Embedding**: An Embedding Model converts each split into vectors (embeddings) that capture the semantic meaning of the text ... .

- **Vector Store**: These embeddings, along with their corresponding text, are stored in a specialized database called a Vector Store (e.g., Faiss or Chroma) s s .

- **Retrieval**: The Retriever component converts the user's question into its own vector s s .

- **Similarity Search**: The query vector is compared against all stored vectors to find the semantically closest ones (e.g., top 4 similar results) ... .

- **Response Generation**: The retrieved relevant text chunks (context) and the original query are packaged into a prompt and sent to the LLM, which combines this context with its parametric knowledge to generate the final response ... .


## Implementing RAG as a LangGraph Tool
## Strategy and Preparation
- In agentic AI applications, RAG is generally implemented by defining it as a tool within the LangGraph framework s s .

**Document Ingestion Steps (Preparation Phase):**
- Load the PDF document using a loader (e.g., PyPDFLoader) s s .
- Split the document into chunks using a RecursiveCharacterTextSplitter, specifying chunk size and overlap to maintain context s s .
- Define an embedding model (e.g., text-embedding-3-small) s s .
- Create a Vector Store (e.g., Faiss) by passing the chunks and the embedding model, which generates and saves the embeddings ... .
- Create a Retriever object from the Vector Store, configured for similarity searching and specifying the number of top results to retrieve (e.g., 4) s s .

**RAG Tool Definition and Functionality**
- The RAG functionality is wrapped in a function decorated as a LangGraph Tool (`@tool`) s .

- The tool's core logic calls `retriever.invoke(query)`, which performs the similarity search and fetches the most relevant document chunks (context) s s .

- The tool extracts the page_content and metadata from the retrieved documents and organizes them into a dictionary (containing the original query, context, and metadata) to be passed back to the LLM ... .

- This RAG tool is added to the list of available tools and bound to the LLM s .

**LangGraph Flow**
- The graph uses a *Chat Node* and a *Tool Node* s s .

- The Chat Node receives the question and makes a decision: if the question requires external knowledge (RAG), control is passed to the Tool Node  .

- The Tool Node executes the RAG tool, retrieves the relevant documents/context, and sends this context back to the Chat Node  .

- The Chat Node then uses the retrieved context along with the original query to generate the final, grounded answer.


![LangGraph RAG Tool Flow](/LangGraph_Advanced/Advanced%20topics/with%20rag/images/LangGraph%20RAG%20Tool%20Flow.png)


- The process can be visualized (e.g., using LangSmith) to confirm that the Chat Node correctly calls the RAG Tool with the query, the Tool Node returns the retrieved chunks, and the Chat Node synthesizes the final answer based on those chunks ... .

## Integration into Existing Project Code
- For the existing multi-utility chatbot, the RAG integration required defining a new back-end function, ingest_pdf, which handles all the document loading, splitting, embedding, and retriever creation .

- The RAG Tool definition was added to the existing tool definitions (Search, Calculator, Stock Price) s .

- The front-end code was modified to include an additional component in the sidebar to allow users to upload PDF files for ingestion s .

> Treating RAG as another tool simplifies the integration into complex agentic AI applications s .



