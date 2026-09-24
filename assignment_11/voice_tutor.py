"""Assignment 11: speech-controlled ICT and Azure tutor.

The application records one spoken question, transcribes it, asks an AI tutor,
and reads the answer aloud.  Each stage is timed and written to CSV.
"""
from __future__ import annotations

import csv
import os
import tempfile
import time
import wave
from pathlib import Path

import numpy as np
import sounddevice as sd
import soundfile as sf
from dotenv import load_dotenv
from openai import APIConnectionError, APIStatusError, OpenAI

SAMPLE_RATE = 16_000
CHANNELS = 1
BLOCK_SECONDS = 0.20
SILENCE_RMS = 0.012       # Adjust if the room is unusually noisy/quiet.
SILENCE_AFTER_SPEECH = 1.2
MAX_RECORD_SECONDS = 20
LOG_FILE = Path("conversation_log.csv")

SYSTEM_PROMPT = """You are a concise Finnish ICT and Azure tutor. Answer in Finnish.
Explain technical terms plainly, give one practical example, and keep every answer
under 90 words. If the question is unclear, ask one short follow-up question."""


def rms(block: np.ndarray) -> float:
    """Return the signal volume used for simple voice-activity detection."""
    return float(np.sqrt(np.mean(np.square(block))))


def record_until_silence(destination: Path) -> float:
    """Record until the speaker has finished, detected as sustained silence."""
    blocks: list[np.ndarray] = []
    spoken = False
    silent_for = 0.0
    started = time.perf_counter()

    print("\nPuhu nyt. Tallennus päättyy noin 1,2 s hiljaisuuden jälkeen.")
    try:
        with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS,
                            dtype="float32", blocksize=int(SAMPLE_RATE * BLOCK_SECONDS)) as stream:
            while time.perf_counter() - started < MAX_RECORD_SECONDS:
                block, _overflowed = stream.read(int(SAMPLE_RATE * BLOCK_SECONDS))
                blocks.append(block.copy())
                if rms(block) >= SILENCE_RMS:
                    spoken = True
                    silent_for = 0.0
                elif spoken:
                    silent_for += BLOCK_SECONDS
                    if silent_for >= SILENCE_AFTER_SPEECH:
                        break
    except sd.PortAudioError as exc:
        raise RuntimeError(f"Mikrofonia ei voitu käyttää: {exc}") from exc

    if not spoken:
        raise RuntimeError("Puhetta ei havaittu. Tarkista mikrofoni tai SILENCE_RMS-arvo.")
    audio = np.concatenate(blocks, axis=0)
    sf.write(destination, audio, SAMPLE_RATE, subtype="PCM_16")
    return time.perf_counter() - started


def transcribe(client: OpenAI, wav_path: Path) -> str:
    with wav_path.open("rb") as audio_file:
        result = client.audio.transcriptions.create(
            model="gpt-4o-transcribe", file=audio_file, language="fi"
        )
    return result.text.strip()


def ask_tutor(client: OpenAI, question: str) -> str:
    result = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "system", "content": SYSTEM_PROMPT},
                  {"role": "user", "content": question}],
        temperature=0.3,
    )
    return result.choices[0].message.content.strip()


def speak(client: OpenAI, text: str, mp3_path: Path) -> None:
    with client.audio.speech.with_streaming_response.create(
        model="gpt-4o-mini-tts", voice="coral", input=text,
        instructions="Puhu selkeää, rauhallista suomea."
    ) as response:
        response.stream_to_file(mp3_path)


def play(mp3_path: Path) -> None:
    data, sample_rate = sf.read(mp3_path, dtype="float32")
    sd.play(data, sample_rate)
    sd.wait()


def append_log(row: dict[str, object]) -> None:
    new_file = not LOG_FILE.exists()
    with LOG_FILE.open("a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=row.keys())
        if new_file:
            writer.writeheader()
        writer.writerow(row)


def timed(call):
    started = time.perf_counter()
    value = call()
    return value, time.perf_counter() - started


def main() -> None:
    load_dotenv(override=True)
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY puuttuu. Lisää se .env-tiedostoon.")
    client = OpenAI()
    print("=== Puheohjattu ICT-/Azure-tutor ===")
    print("Sano 'lopeta', kun haluat lopettaa. Käytä kuulokkeita kaiun vähentämiseksi.")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp = Path(temp_dir)
        while True:
            input("\nPaina Enter ja kysy kysymyksesi...")
            wav_path, mp3_path = temp / "question.wav", temp / "answer.mp3"
            try:
                _record_time = record_until_silence(wav_path)
                transcript, stt_s = timed(lambda: transcribe(client, wav_path))
                print(f"Tunnistettu: {transcript}")
                if "lopeta" in transcript.lower():
                    print("Istunto päättyy.")
                    break
                answer, llm_s = timed(lambda: ask_tutor(client, transcript))
                print(f"Tutor: {answer}")
                _, tts_s = timed(lambda: speak(client, answer, mp3_path))
                play(mp3_path)
                total_s = stt_s + llm_s + tts_s
                append_log({"question": transcript, "stt_s": round(stt_s, 2),
                            "llm_s": round(llm_s, 2), "tts_s": round(tts_s, 2),
                            "total_after_speech_s": round(total_s, 2)})
                print(f"Viiveet: STT {stt_s:.2f} s | LLM {llm_s:.2f} s | TTS {tts_s:.2f} s | yhteensä {total_s:.2f} s")
            except (RuntimeError, APIConnectionError, APIStatusError) as exc:
                print(f"Virhe: {exc}. Yritä uudelleen.")
            except KeyboardInterrupt:
                print("\nKeskeytetty. Istunto päättyy.")
                break


if __name__ == "__main__":
    main()
