# Assignment 10 – Voice Interpreter

Python application for the pipeline:

`English speech → STT → English text → French translation → TTS → French speech`

## Setup on Windows PowerShell

```powershell
cd C:\Web\voice_interpreter
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
```

In `.env`, add your own OpenAI key after `OPENAI_API_KEY=`. Never upload `.env` to GitHub.

## Run

```powershell
python voice_interpreter.py
```

Press Enter, speak an English sentence, then pause. The application records at 16 kHz mono, detects the end of speech after about 1.2 seconds of silence, transcribes English speech, translates it into French, creates French speech and plays it.

Each successful turn is appended to `conversation_log.csv`.

After at least five successful turns, run:

```powershell
python show_results.py
```

This prints the latency of every run plus fastest, median and slowest end-of-speech-to-playback latency.

## Models

- STT: `gpt-4o-transcribe`
- Translation: `gpt-4.1-mini`
- TTS: `gpt-4o-mini-tts`

## Files to upload to GitHub

- `voice_interpreter.py`
- `show_results.py`
- `requirements.txt`
- `README.md`
- `conversation_log.csv` after testing
- PowerShell screenshots after testing

Do not upload `.env`, `question.wav` or `translation.wav`.
