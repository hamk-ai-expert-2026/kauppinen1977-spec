"""Print a five-run latency summary from conversation_log.csv."""

import csv
import statistics
from pathlib import Path

LOG_FILE = Path("conversation_log.csv")


def values(rows: list[dict[str, str]], column: str) -> list[float]:
    return [float(row[column]) for row in rows]


def main() -> None:
    if not LOG_FILE.exists():
        print("conversation_log.csv was not found. Run voice_interpreter.py first.")
        return

    with LOG_FILE.open(encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))

    if len(rows) < 5:
        print(f"There are only {len(rows)} successful tests. Run the interpreter at least five times.")
        return

    print("\n" + "=" * 78)
    print("                       LATENCY SUMMARY")
    print("=" * 78)
    print(f"{'Run':<5} {'STT':>8} {'Translate':>11} {'TTS first':>11} {'To playback':>14}")

    for number, row in enumerate(rows, start=1):
        print(
            f"{number:<5} {float(row['stt_s']):>7.2f}s "
            f"{float(row['translation_s']):>10.2f}s "
            f"{float(row['tts_first_audio_s']):>10.2f}s "
            f"{float(row['end_to_playback_s']):>13.2f}s"
        )

    totals = values(rows, "end_to_playback_s")
    print("-" * 78)
    print(f"STT delay (median):                 {statistics.median(values(rows, 'stt_s')):.2f} s")
    print(f"Translation/LLM delay (median):     {statistics.median(values(rows, 'translation_s')):.2f} s")
    print(f"TTS time-to-first-audio (median):   {statistics.median(values(rows, 'tts_first_audio_s')):.2f} s")
    print(f"Total end-to-playback (median):     {statistics.median(totals):.2f} s")
    print(f"Fastest run:                        {min(totals):.2f} s")
    print(f"Median run:                         {statistics.median(totals):.2f} s")
    print(f"Slowest run:                        {max(totals):.2f} s")
    print("=" * 78)
    print("Results read from conversation_log.csv")


if __name__ == "__main__":
    main()
