"""Assignment 10: English-to-French voice interpreter."""

import csv
import os
import time
import wave
from pathlib import Path

import numpy as np
import sounddevice as sd
import soundfile as sf
from dotenv import load_dotenv
from openai import APIConnectionError, APIError, AuthenticationError, OpenAI

SAMPLE_RATE = 16_000
CHANNELS = 1
BLOCKSIZE = 1_024
SILENCE_RMS = 0.012
SILENCE_SECONDS = 1.2
MAX_WAIT_SECONDS = 12

WAV_INPUT = Path("question.wav")
WAV_OUTPUT = Path("translation.wav")
LOG_FILE = Path("conversation_log.csv")


def rms(samples: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(samples, dtype=np.float64))))


def record_question() -> float:
    """Record until the user has spoken and then pauses for SILENCE_SECONDS.

    Returns the perf_counter timestamp representing the end of speech.
    """
    audio_blocks: list[np.ndarray] = []
    speech_started = False
    silent_seconds = 0.0
    started_at = time.perf_counter()

    print("Speak English now. Recording ends after about 1.2 s of silence.")
    try:
        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="float32",
            blocksize=BLOCKSIZE,
        ) as stream:
            while True:
                block, _overflowed = stream.read(BLOCKSIZE)
                audio_blocks.append(block.copy())
                volume = rms(block)
                elapsed = time.perf_counter() - started_at

                if volume >= SILENCE_RMS:
                    speech_started = True
                    silent_seconds = 0.0
                elif speech_started:
                    silent_seconds += len(block) / SAMPLE_RATE

                if speech_started and silent_seconds >= SILENCE_SECONDS:
                    break
                if not speech_started and elapsed >= MAX_WAIT_SECONDS:
                    raise RuntimeError("No speech was detected. Check the microphone or SILENCE_RMS.")
    except sd.PortAudioError as error:
        raise RuntimeError(f"Microphone error: {error}") from error

    recording = np.concatenate(audio_blocks, axis=0)
    sf.write(WAV_INPUT, recording, SAMPLE_RATE, subtype="PCM_16")
    return time.perf_counter()


def transcribe(client: OpenAI) -> tuple[str, float]:
    started = time.perf_counter()
    with WAV_INPUT.open("rb") as audio_file:
        result = client.audio.transcriptions.create(
            model="gpt-4o-transcribe",
            file=audio_file,
            language="en",
            prompt=(
                "The speaker is using Finnish-accented English. This is a short English "
                "question or sentence. Transcribe only in normal English spelling and "
                "punctuation; do not use phonetic spelling or translate the speech."
            ),
        )
    text = result.text.strip()
    if not text:
        raise RuntimeError("The transcription was empty.")
    return text, time.perf_counter() - started


def translate(client: OpenAI, source_text: str) -> tuple[str, float]:
    started = time.perf_counter()
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a precise interpreter. Translate the user's English text "
                    "into natural French. Return only the French translation, with no "
                    "explanation, quotation marks or labels."
                ),
            },
            {"role": "user", "content": source_text},
        ],
        temperature=0,
    )
    translation = (response.choices[0].message.content or "").strip()
    if not translation:
        raise RuntimeError("The translation response was empty.")
    return translation, time.perf_counter() - started


def create_speech(client: OpenAI, french_text: str) -> tuple[float, float]:
    """Create a WAV file and return (time_to_first_audio, full_tts_time)."""
    started = time.perf_counter()
    first_audio_time: float | None = None

    with client.audio.speech.with_streaming_response.create(
        model="gpt-4o-mini-tts",
        voice="coral",
        input=french_text,
        response_format="wav",
        instructions="Speak clearly and naturally in French.",
    ) as response:
        with WAV_OUTPUT.open("wb") as output_file:
            for chunk in response.iter_bytes(chunk_size=8_192):
                if chunk:
                    if first_audio_time is None:
                        first_audio_time = time.perf_counter()
                    output_file.write(chunk)

    finished = time.perf_counter()
    if first_audio_time is None:
        raise RuntimeError("The text-to-speech response contained no audio.")
    return first_audio_time - started, finished - started


def play_audio() -> None:
    data, sample_rate = sf.read(WAV_OUTPUT, dtype="float32")
    sd.play(data, sample_rate)
    sd.wait()


def save_log(row: dict[str, object]) -> None:
    exists = LOG_FILE.exists()
    with LOG_FILE.open("a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(row.keys()))
        if not exists:
            writer.writeheader()
        writer.writerow(row)


def main() -> None:
    load_dotenv(override=True)
    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY is missing. Create a .env file from .env.example.")
        return

    client = OpenAI()
    print("=== English to French Voice Interpreter ===")
    print("Say 'quit' or press Ctrl + C to stop after a completed turn.")

    while True:
        try:
            input("\nPress Enter, then speak your English sentence...")
            end_of_speech = record_question()
            english, stt_s = transcribe(client)
            print(f"English: {english}")

            if english.lower().strip(".!? ") in {"quit", "exit", "stop"}:
                print("Goodbye!")
                break

            french, translation_s = translate(client, english)
            print(f"French:  {french}")

            tts_ttfb_s, tts_full_s = create_speech(client, french)
            playback_started = time.perf_counter()
            to_playback_s = playback_started - end_of_speech
            play_audio()

            row = {
                "english_text": english,
                "french_text": french,
                "stt_s": f"{stt_s:.3f}",
                "translation_s": f"{translation_s:.3f}",
                "tts_first_audio_s": f"{tts_ttfb_s:.3f}",
                "tts_full_s": f"{tts_full_s:.3f}",
                "end_to_playback_s": f"{to_playback_s:.3f}",
            }
            save_log(row)
            print(
                "Latency: "
                f"STT {stt_s:.2f}s | translation {translation_s:.2f}s | "
                f"TTS first audio {tts_ttfb_s:.2f}s | "
                f"end-to-playback {to_playback_s:.2f}s"
            )
            print("Saved to conversation_log.csv")

        except AuthenticationError:
            print("Error: the OpenAI API key is invalid or expired. Check .env and try again.")
        except APIConnectionError:
            print("Error: network connection to OpenAI failed. Check your connection and try again.")
        except APIError as error:
            print(f"OpenAI API error: {error}")
        except (RuntimeError, OSError, wave.Error) as error:
            print(f"Error: {error}")
        except KeyboardInterrupt:
            print("\nStopped by user.")
            break


if __name__ == "__main__":
    main()
