import csv
import statistics

with open("conversation_log.csv", encoding="utf-8") as file:
    rows = list(csv.DictReader(file))

if len(rows) < 5:
    print(f"Testeja on vasta {len(rows)}. Aja ohjelma vähintään 5 kertaa.")
    raise SystemExit

print("\n" + "=" * 62)
print("                LATENCY SUMMARY / VIIVEYHTEENVETO")
print("=" * 62)
print(f"{'Ajo':<5} {'STT':>8} {'LLM':>8} {'TTS':>8} {'Yhteensä':>12}")

totals = []

for number, row in enumerate(rows, start=1):
    stt = float(row["stt_s"])
    llm = float(row["llm_s"])
    tts = float(row["tts_s"])
    total = float(row["total_after_speech_s"])
    totals.append(total)

    print(f"{number:<5} {stt:>7.2f}s {llm:>7.2f}s {tts:>7.2f}s {total:>11.2f}s")

print("-" * 62)
print(f"Nopein ajo:  {min(totals):.2f} s")
print(f"Mediaaniajo: {statistics.median(totals):.2f} s")
print(f"Hitain ajo:  {max(totals):.2f} s")
print("=" * 62)
print("Tulokset luettu tiedostosta conversation_log.csv")