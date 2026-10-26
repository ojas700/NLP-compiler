# NLP Compiler
### AI-Assisted Natural Language Compiler with Intermediate Language Translation and C Code Generation

## Overview

NLP Compiler is a compiler project that translates English-like instructions into executable C programs through an AI-assisted natural language understanding stage and a deterministic compilation pipeline.

The system uses Qwen 2.5 3B through Ollama to interpret natural language instructions and convert them into structured intent JSON. The intent is validated and translated into an intermediate language (IL), which is processed by the compiler pipeline to generate C code.

## Architecture

**Natural Language Input → Qwen NLU → Intent JSON → Validation → Intermediate Language → Lexer → Parser → Symbol Table → Semantic Analysis → Intermediate Representation → C Code Generation → GCC Compilation and Execution**

The language model is restricted to natural-language interpretation. The subsequent compiler stages use deterministic logic rather than relying on the language model to generate compiler code.

## Key Features

- Natural-language instruction processing
- AI-assisted intent extraction using Qwen 2.5 3B
- Structured intent validation and IL translation
- Lexical and syntax analysis
- Symbol table management and semantic checks
- Intermediate representation and C code generation
- Compilation and execution using GCC/MinGW
- Web-based compiler interface
- Voice input and multilingual support, subject to browser and application capabilities

## Technology Stack

- **Language Model:** Qwen 2.5 3B
- **Local Model Runtime:** Ollama
- **Compiler Implementation:** C
- **Application and Integration:** Python
- **Frontend:** HTML, CSS, JavaScript
- **Native Compilation:** GCC/MinGW

## Project Structure

- `ai/` — AI interpretation, intent validation, and IL translation components
- `compiler/` — Compiler implementation
- `grammar/` — Grammar-related files
- `gui/` — User interface components
- `scratch/` — Supporting scripts and experiments
- `app.py` — Application entry point

## Running the Project

The application uses a local Ollama model and a native C compiler. To run it:

1. Install Python, Ollama, and GCC/MinGW.
2. Download the required Qwen model using Ollama:

   ```bash
   ollama pull qwen2.5:3b
   ```

3. Start Ollama and ensure the model is available.
4. Install the Python dependencies listed in the project's dependency files, if provided.
5. Follow the application's startup instructions and run the Python application from the project directory.

Exact commands may depend on the project's current configuration.

## Academic Context

Developed as a Compiler Design project to explore the integration of natural language understanding with conventional compiler design, deterministic intermediate representations, semantic validation, and C code generation.

## Repository

GitHub: https://github.com/ojas700/NLP-compiler
