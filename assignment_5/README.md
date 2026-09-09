Make: Ville Kauppinen
Programs: PowerShell -> LM Studio
LLM: qwen/qwen3.8-27b
Link: https://github.com/hamk-ai-expert-2026/kauppinen1977-spec

Implementation

I created a standalone Python command-line application called `assignment_5.py`. The program asks the user for a word or technical term and generates a schema-validated dictionary entry.

The application runs locally through LM Studio, which provides an OpenAI-compatible API endpoint. Python sends an HTTP request to the local LM Studio server using the Qwen 3.8 27B model.

The required output structure is defined with a Pydantic `DictionaryEntry` model. Each entry contains:

• the word;
• one or more definitions;
• a list of synonyms;
• a list of antonyms;
• one or more example sentences.

The application sends a JSON Schema to LM Studio through the `response_format` parameter. The returned JSON is parsed and validated with Pydantic before it is shown to the user. Empty definition and example lists are rejected, while empty synonym or antonym lists are accepted when a genuine semantic equivalent or opposite does not exist.

For example, the word “tulostin” can have synonyms such as “tulostuslaite”, but it does not normally have a meaningful antonym. During testing, I also handled a Qwen-specific behaviour where the JSON response can be returned in `reasoning_content` instead of the normal `content` field.
