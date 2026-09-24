# Tehtävä 11 – puheohjattu ICT-/Azure-tutor

## Idea

Ohjelma on suomenkielinen AI-tutor. Käyttäjä kysyy esimerkiksi: *"Mitä RBAC tekee Azuressa?"* Ohjelma tunnistaa puheen, lähettää tekstin kielimallille ja lukee vastauksen ääneen.

```text
Mikrofoni → hiljaisuuden tunnistus → puheentunnistus → AI-tutor → puhesynteesi → kaiutin
```

## Käyttöönotto

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows PowerShellissä: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env          # Windowsissa
python voice_tutor.py
```

Lisää oma API-avain `.env`-tiedostoon. Älä tallenna avainta GitHubiin tai palautukseen.

## Mitä ohjelmassa on tehty

1. `sounddevice` avaa mikrofonin 16 kHz monoääntä varten.
2. Ohjelma laskee jokaisen 0,2 sekunnin äänipalan RMS-voimakkuuden. Kun puhe on alkanut ja hiljaisuutta kestää 1,2 sekuntia, tallennus päättyy. Tämä on kevyt VAD-ratkaisu.
3. Ääni tallennetaan väliaikaiseksi WAV-tiedostoksi ja `gpt-4o-transcribe` muuttaa sen suomenkieliseksi tekstiksi.
4. `gpt-4.1-mini` toimii rajattuna ICT-/Azure-tutorina. Järjestelmäohje määrää vastaamaan suomeksi, selkeästi ja lyhyesti.
5. `gpt-4o-mini-tts` tekee vastauksesta MP3-äänen, joka soitetaan `sounddevice`-kirjastolla.
6. `time.perf_counter()` mittaa STT-, LLM- ja TTS-vaiheen. Tulokset tallennetaan `conversation_log.csv`-tiedostoon viittä testiajoa ja mediaanin laskentaa varten.
7. Mikrofonin, verkon ja API:n virheet käsitellään niin, että ohjelma ei kaadu vaan pyytää uutta yritystä.

## Arviointi ja testit

Aja ohjelma vähintään viisi kertaa eri kysymyksillä ja liitä palautukseen `conversation_log.csv` sekä esimerkiksi tämä taulukko.

| Arvioitava asia | Havainto omissa testeissä |
|---|---|
| Vasteviive | Täytä CSV-lokista nopein, mediaani ja hitain kokonaisviive. |
| Tunnistusvirheet | Testaa tekniset sanat kuten *Entra ID*, *RBAC* ja *VM*. |
| Taustamelu | Testaa hiljaisessa huoneessa ja taustamusiikin/puheen kanssa. |
| Keskeytykset | Tämä perusversio ei tue keskeytystä puhesynteesin aikana. |
| Kaiku | Kaiutin voi päätyä takaisin mikrofoniin; kuulokkeet pienentävät riskiä. |
| Verkkovirhe | API- ja yhteysvirhe näytetään käyttäjälle, jonka jälkeen uusi kysymys onnistuu. |
| Puheenvuoron loppu | 1,2 s hiljaisuus toimii tavallisissa kysymyksissä, mutta voi katkaista hitaasti puhuvan käyttäjän. |

## Kehitysidea

Seuraava versio käyttäisi WebSocket-pohjaista reaaliaikaista audio-APIa. Tällöin STT, vastaus ja TTS voisivat virrata samanaikaisesti ja käyttäjä voisi keskeyttää vastauksen puhumalla. Nykyinen tiedosto kerrallaan -toteutus on tarkoituksella selkeä ja helposti testattava perusratkaisu.
