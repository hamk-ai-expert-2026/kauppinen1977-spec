"""Generate product marketing content from product images and optional facts.

The application sends one or more local images to OpenAI's Responses API.
It deliberately separates visual observations from user-provided facts so that
the model is instructed not to invent product specifications.
"""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


API_URL = "https://api.openai.com/v1/responses"
MODEL = "gpt-5.6-luna"
SUPPORTED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}


def image_to_data_url(filename: str | Path) -> str:
    """Convert a supported local image to a Base64 data URL."""
    path = Path(filename)
    if not path.is_file():
        raise FileNotFoundError(f"Image not found: {path}")

    mime_type, _ = mimetypes.guess_type(path.name)
    if mime_type not in SUPPORTED_MIME_TYPES:
        supported = ", ".join(sorted(SUPPORTED_MIME_TYPES))
        raise ValueError(f"Unsupported image type for {path.name}: {mime_type}. Supported: {supported}")

    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def build_prompt(info: str, language: str, tone: str, slogans: int) -> str:
    supplied_info = info.strip() if info.strip() else "No additional product information was supplied."
    return f"""You are a careful product-marketing assistant.

Analyze the supplied product images and create marketing content in {language}.
Use a {tone} tone.

Critical factual rules:
- Clearly distinguish image observations from user-provided facts.
- Do not invent specifications, dimensions, capacity, materials, certifications,
  performance claims, brand, warranty, compatibility or safety claims.
- A statement is allowed only when it is visibly supported by the images or
  explicitly stated in the user-provided information.
- If a package contains text that is difficult to read, do not guess what it says.

User-provided information:
{supplied_info}

Return plain text using exactly these headings:

Product Description:
Write one concise paragraph. Attribute supplied facts using wording such as
"According to the supplied product information" when appropriate.

Marketing Slogans:
Write exactly {slogans} short slogans, each starting with "- ".

Visible in Images:
Write bullet points for visual observations only.

User-provided Facts:
Write bullet points for facts from the supplied information only. If none were
provided, write "- No additional facts supplied."
"""


def call_openai(image_filenames: list[str], prompt: str) -> str:
    """Call the Responses API without the OpenAI SDK."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set in the environment.")

    content: list[dict[str, str]] = [{"type": "input_text", "text": prompt}]
    for filename in image_filenames:
        content.append({"type": "input_image", "image_url": image_to_data_url(filename)})

    payload = {
        "model": MODEL,
        "input": [{"role": "user", "content": content}],
    }
    request = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI API error {exc.code}: {error_body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Network error while calling OpenAI: {exc.reason}") from exc

    # Some Responses API replies include the convenience ``output_text`` field,
    # while others return the text only inside output -> content. Support both.
    output_text = result.get("output_text", "").strip()
    if not output_text:
        text_parts: list[str] = []
        for item in result.get("output", []):
            for content_item in item.get("content", []):
                if content_item.get("type") == "output_text":
                    text = content_item.get("text", "")
                    if text:
                        text_parts.append(text)
        output_text = "\n".join(text_parts).strip()

    if not output_text:
        raise RuntimeError("The model returned no readable text response.")
    return output_text


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate factual product marketing content from one or more product images."
    )
    parser.add_argument("--images", nargs="+", required=True, help="One or more JPEG, PNG or WebP images.")
    parser.add_argument("--info", default="", help="Optional factual product information supplied by the user.")
    parser.add_argument("--language", default="Finnish", help="Output language (default: Finnish).")
    parser.add_argument("--tone", default="professional", help="Marketing tone (default: professional).")
    parser.add_argument("--slogans", type=int, default=4, help="Number of slogans, 1-10 (default: 4).")
    parser.add_argument("--output", help="Optional UTF-8 text file for saving the generated content.")
    args = parser.parse_args()

    if not 1 <= args.slogans <= 10:
        parser.error("--slogans must be between 1 and 10.")
    return args


def main() -> None:
    args = parse_arguments()
    prompt = build_prompt(args.info, args.language, args.tone, args.slogans)
    generated_text = call_openai(args.images, prompt)

    print(generated_text)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(generated_text + "\n", encoding="utf-8")
        print(f"\nSaved output: {output_path.resolve()}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError) as exc:
        raise SystemExit(f"Error: {exc}") from exc
