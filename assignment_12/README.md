Valitse Notepadissa kaikki tekstI (`Ctrl + A`) ja korvaa se tällä. Tallenna sitten `Ctrl + S`.



\# Assignment 12 – Local AI Music Generation with ACE-Step 1.5



\*\*Student:\*\* Ville Kauppinen

\*\*Tool and model:\*\* ACE-Step 1.5, `acestep-v15-turbo`

\*\*Execution environment:\*\* Windows, Python/UV, NVIDIA GeForce RTX 3050 Laptop GPU (6 GB VRAM)



\## Overview



This project demonstrates local AI music generation with the open-source ACE-Step 1.5 model. I generated a complete two-minute instrumental music piece on my own Windows computer.



The model detected the 6 GB NVIDIA GPU and used CPU offload and INT8 weight-only quantization to fit the model into the available VRAM.



\## Generated music



\* File: `output/ace\_step\_nordic\_ambient.wav`

\* Format: WAV, 16-bit

\* Duration: 2:00

\* Generation time: 12.54 seconds

\* Mode: Custom

\* Instrumental: enabled



WAV was selected because the local Windows application policy blocked the `ffmpeg.exe` executable that ACE-Step needs for MP3 export.



\## Prompt



```text

Instrumental Nordic cinematic ambient music, slow expressive piano melody, warm analog synthesizer pads, gentle legato strings, subtle electronic percussion, calm winter evening atmosphere, polished studio sound.

```



The same prompt is also available in `prompt.txt`.



\## How to run ACE-Step locally



The original ACE-Step repository was cloned separately from:



\[https://github.com/ACE-Step/ACE-Step-1.5](https://github.com/ACE-Step/ACE-Step-1.5)



From the ACE-Step project folder, install the required packages:



```powershell

uv sync

```



Start the local ACE-Step web interface:



```powershell

uv run acestep --init\_service true --config\_path acestep-v15-turbo --init\_llm false --batch\_size 1

```



Open the local address displayed in PowerShell, normally:



```text

http://127.0.0.1:7860

```



The launcher command is also stored in `code/start\_ace\_step.ps1`.



\## Evidence



\* `screenshots/prompt\_and\_settings.jpg` shows the prompt, Custom mode and Instrumental option.

\* `screenshots/generation\_complete.jpg` shows the generated waveform and the completed generation status.

\* `output/ace\_step\_nordic\_ambient.wav` is the generated example song.



\## Repository structure



```text

assignment\_12/

├── README.md

├── prompt.txt

├── code/

│   └── start\_ace\_step.ps1

├── output/

│   └── ace\_step\_nordic\_ambient.wav

└── screenshots/

&#x20;   ├── prompt\_and\_settings.jpg

&#x20;   └── generation\_complete.jpg

```



