# AI RAG System - Mathematics PDF Chatbot

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35-red.svg)](https://streamlit.io)
[![LangChain](https://img.shields.io/badge/LangChain-0.3-green.svg)](https://langchain.com)
[![Gemini](https://img.shields.io/badge/Gemini-2.5-orange.svg)](https://ai.google.dev)




A **Retrieval-Augmented Generation (RAG)** chatbot that answers questions about a mathematics PDF using Google's Gemini AI, FAISS vector search, and LangChain orchestration.

## Table of Contents
- [Features](#features)
- [Demo](#demo)
- [Tech Stack](#tech-stack)
- [Installation](#installation)
- [Usage](#usage)
- [Recent Updates](#recent-updates)
- [Project Structure](#project-structure)
- [Author](#author)

##  Features

- **PDF Processing** - Loads and processes mathematics PDF documents
- **Semantic Chunking** - Uses intelligent chunking instead of fixed-size chunks
- **Vector Search** - FAISS-based similarity search for relevant context
- **Gemini AI Integration** - Uses Gemini 2.5 Flash for chat and Gemini Embedding 2 for vectors
- **Interactive UI** - Clean Streamlit chat interface with conversation history
- **Secure API Key Management** - Uses `.env` file for sensitive credentials

## Demo

### Chat Interface

![RAG Chatbot Demo](images/dashboard.png)

## Sample Interaction

### Question:
**What are the two main aspects of SHA-512 that this article proposes to modify?**

### Answer:
This article proposes to modify SHA-512 in two main aspects:
1. The modification of original hash buffer values.
2. The modification of additive constants \( K_2 \).


##  Tech Stack

| Category | Technology |
|----------|------------|
| **Framework** | Streamlit |
| **LLM** | Google Gemini 2.5 Flash |
| **Embeddings** | Google Gemini Embedding 2 (preview) |
| **Vector Store** | FAISS |
| **Orchestration** | LangChain |
| **Chunking** | SemanticChunker (LangChain Experimental) |
| **PDF Processing** | PyPDFLoader |

##  Installation

### Prerequisites
- Python 3.11 or higher
- Google Gemini API key ([Get it here](https://aistudio.google.com/))

### Steps

1. **Clone the repository**
```bash
git clone https://github.com/tharindinuja-lang/ai-rag-assignment.git
cd ai-rag-assignment
