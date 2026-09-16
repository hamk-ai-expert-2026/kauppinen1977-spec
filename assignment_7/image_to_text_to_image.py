"""Exercise 7: Image -> Text -> Image (final direct HTTPS version).

This version uses Python's standard library for HTTPS requests. It therefore
does not require the OpenAI Python SDK or its native ``jiter`` dependency.
"""

from __future__ import annotations

import argparse
import base64
import binascii
import json
import mimetypes
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


API_BASE_URL = "https://api.openai.com/v1"
VISION_MODEL = "gpt-5.6-luna"
IMAGE_MODEL = "gpt-image-2"
SUPPORTED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}


def image_to_data_url(filename: Path) -> str:
    if not filename.is_file():
        raise FileNotFoundError(f"Input image was not found: {filename}")

    mime_type, _ = mimetypes.guess_type(filename.name)
    if mime_type not in SUPPORTED_MIME_TYPES:
        supported = ", ".join(sorted(SUPPORTED_MIME_TYPES))
        raise ValueError(
            f"Unsupported image type: {mime_type or 'unknown'}. "
            f"Supported types: {supported}"
        )

    encoded = base64.b64encode(filename.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def post_json(endpoint: str, payload: dict, api_key: str) -> dict:
    request = Request(
        url=f"{API_BASE_URL}{endpoint}",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=180) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI API error {exc.code}: {details}") from exc
    except URLError as exc:
        raise RuntimeError(f"Network error when calling OpenAI: {exc.reason}") from exc


def extract_response_text(response: dict) -> str:
    """Extract the first text output from a Responses API JSON response."""
    for item in response.get("output", []):
        for content in item.get("content", []):
            if content.get("type") == "output_text" and content.get("text"):
                return content["text"].strip()
    raise RuntimeError("The vision model returned no text description.")


def describe_image(image_path: Path, api_key: str) -> str:
    payload = {
        "model": VISION_MODEL,
        "input": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": (
                            "Describe the supplied image as one detailed English prompt "
                            "for an image-generation model. Describe only visible content: "
                            "main subject, setting, composition, colours, lighting, camera "
                            "angle and mood. Do not invent text, brands or facts. Return only "
                            "the prompt."
                        ),
                    },
                    {"type": "input_image", "image_url": image_to_data_url(image_path)},
                ],
            }
        ],
    }
    return extract_response_text(post_json("/responses", payload, api_key))


def generate_image(prompt: str, output_path: Path, api_key: str) -> None:
    payload = {
        "model": IMAGE_MODEL,
        "prompt": prompt,
        "size": "1536x1024",
        "quality": "medium",
        "n": 1,
    }
    response = post_json("/images/generations", payload, api_key)
    try:
        encoded_image = response["data"][0]["b64_json"]
        image_bytes = base64.b64decode(encoded_image, validate=True)
    except (KeyError, IndexError, TypeError, binascii.Error) as exc:
        raise RuntimeError("The image API returned invalid image data.") from exc

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(image_bytes)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyse an image, then generate a new image from its description."
    )
    parser.add_argument("--input", required=True, type=Path, help="Input image path")
    parser.add_argument(
        "--output", required=True, type=Path, help="Output image path (.png)"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_arguments()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set.")

    print(f"Analysing: {args.input}")
    description = describe_image(args.input, api_key)
    print("\nGenerated description:\n")
    print(description)

    print(f"\nGenerating a new image with {IMAGE_MODEL}...")
    generate_image(description, args.output, api_key)
    print(f"Saved generated image: {args.output.resolve()}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError) as exc:
        raise SystemExit(f"Error: {exc}") from exc
