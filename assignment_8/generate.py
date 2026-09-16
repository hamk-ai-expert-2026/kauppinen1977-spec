from __future__ import annotations

import argparse
import base64
import binascii
import io
import os
import re
import sys
import uuid
from datetime import datetime
from pathlib import Path

import requests
from PIL import Image


API_URL = "https://api.openai.com/v1/images/generations"
MODEL = "gpt-image-2"


def non_empty_prompt(value: str) -> str:
    value = value.strip()

    if not value:
        raise argparse.ArgumentTypeError("Prompt cannot be empty.")

    if len(value) > 4000:
        raise argparse.ArgumentTypeError(
            "Prompt is too long. Maximum length is 4000 characters."
        )

    return value


def positive_count(value: str) -> int:
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "Count must be an integer."
        ) from exc

    if not 1 <= number <= 10:
        raise argparse.ArgumentTypeError(
            "Count must be between 1 and 10."
        )

    return number


def parse_aspect_ratio(value: str) -> tuple[int, int]:
    match = re.fullmatch(r"(\d+):(\d+)", value.strip())

    if not match:
        raise argparse.ArgumentTypeError(
            "Aspect ratio must use WIDTH:HEIGHT format, for example 16:9."
        )

    width = int(match.group(1))
    height = int(match.group(2))

    if width <= 0 or height <= 0:
        raise argparse.ArgumentTypeError(
            "Aspect ratio values must be greater than zero."
        )

    if width > 100 or height > 100:
        raise argparse.ArgumentTypeError(
            "Aspect ratio values must not exceed 100."
        )

    return width, height


def choose_api_size(ratio: tuple[int, int]) -> str:
    width, height = ratio
    numeric_ratio = width / height

    if numeric_ratio > 1.05:
        return "1536x1024"

    if numeric_ratio < 0.95:
        return "1024x1536"

    return "1024x1024"


def safe_slug(text: str, maximum_length: int = 40) -> str:
    slug = text.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    slug = slug[:maximum_length].rstrip("-")

    return slug or "generated-image"


def crop_to_aspect_ratio(
    image: Image.Image,
    requested_ratio: tuple[int, int],
) -> Image.Image:
    target_width, target_height = requested_ratio
    target_ratio = target_width / target_height

    current_width, current_height = image.size
    current_ratio = current_width / current_height

    if abs(current_ratio - target_ratio) < 0.001:
        return image

    if current_ratio > target_ratio:
        new_width = round(current_height * target_ratio)
        left = (current_width - new_width) // 2
        box = (
            left,
            0,
            left + new_width,
            current_height,
        )
    else:
        new_height = round(current_width / target_ratio)
        top = (current_height - new_height) // 2
        box = (
            0,
            top,
            current_width,
            top + new_height,
        )

    return image.crop(box)


def extract_image_bytes(
    result_item: dict,
    session: requests.Session,
) -> bytes:
    encoded_image = result_item.get("b64_json")

    if encoded_image:
        try:
            return base64.b64decode(
                encoded_image,
                validate=True,
            )
        except binascii.Error as exc:
            raise RuntimeError(
                "The API returned invalid Base64 image data."
            ) from exc

    temporary_url = result_item.get("url")

    if temporary_url:
        try:
            response = session.get(
                temporary_url,
                timeout=180,
            )
            response.raise_for_status()
            return response.content
        except requests.RequestException as exc:
            raise RuntimeError(
                f"Could not download the generated image: {exc}"
            ) from exc

    raise RuntimeError(
        "The API response contained neither Base64 data nor an image URL."
    )


def generate_one_image(
    session: requests.Session,
    api_key: str,
    prompt: str,
    api_size: str,
    quality: str,
) -> bytes:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "size": api_size,
        "quality": quality,
        "n": 1,
    }

    try:
        response = session.post(
            API_URL,
            headers=headers,
            json=payload,
            timeout=300,
        )
    except requests.RequestException as exc:
        raise RuntimeError(
            f"Network error: {exc}"
        ) from exc

    if not response.ok:
        try:
            error_data = response.json()
            message = error_data.get("error", {}).get(
                "message",
                response.text,
            )
        except ValueError:
            message = response.text

        raise RuntimeError(
            f"API error {response.status_code}: {message}"
        )

    try:
        response_data = response.json()
        image_items = response_data["data"]
        image_item = image_items[0]
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(
            "The API returned an unexpected response."
        ) from exc

    return extract_image_bytes(image_item, session)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate images using the OpenAI Image API."
    )

    parser.add_argument(
        "--prompt",
        required=True,
        type=non_empty_prompt,
        help="Description of the image to generate.",
    )

    parser.add_argument(
        "--aspect-ratio",
        default="1:1",
        type=parse_aspect_ratio,
        metavar="WIDTH:HEIGHT",
        help="Output aspect ratio, for example 1:1, 16:9 or 2:3.",
    )

    parser.add_argument(
        "--count",
        default=1,
        type=positive_count,
        help="Number of images to generate, from 1 to 10.",
    )

    parser.add_argument(
        "--output",
        default=Path("images"),
        type=Path,
        help="Directory in which the generated images are saved.",
    )

    parser.add_argument(
        "--quality",
        default="medium",
        choices=["low", "medium", "high"],
        help="Image quality. Default: medium.",
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY environment variable is not set."
        )

    output_directory: Path = args.output
    output_directory.mkdir(parents=True, exist_ok=True)

    api_size = choose_api_size(args.aspect_ratio)
    ratio_text = f"{args.aspect_ratio[0]}:{args.aspect_ratio[1]}"

    generation_prompt = (
        f"{args.prompt}\n"
        f"Compose the image for a {ratio_text} aspect ratio. "
        "Keep important subjects away from the extreme edges."
    )

    filename_slug = safe_slug(args.prompt)

    print(f"Model: {MODEL}")
    print(f"Requested aspect ratio: {ratio_text}")
    print(f"API image size: {api_size}")
    print(f"Number of images: {args.count}")
    print()

    with requests.Session() as session:
        for index in range(1, args.count + 1):
            print(f"Generating image {index}/{args.count}...")

            image_bytes = generate_one_image(
                session=session,
                api_key=api_key,
                prompt=generation_prompt,
                api_size=api_size,
                quality=args.quality,
            )

            try:
                with Image.open(io.BytesIO(image_bytes)) as image:
                    image.load()
                    image = crop_to_aspect_ratio(
                        image,
                        args.aspect_ratio,
                    )

                    timestamp = datetime.now().strftime(
                        "%Y%m%d-%H%M%S"
                    )
                    unique_part = uuid.uuid4().hex[:8]

                    filename = (
                        f"{filename_slug}-"
                        f"{timestamp}-"
                        f"{unique_part}.png"
                    )

                    output_path = output_directory / filename
                    image.save(output_path, format="PNG")

            except (OSError, ValueError) as exc:
                raise RuntimeError(
                    f"Could not process the generated image: {exc}"
                ) from exc

            print(f"Saved: {output_path.resolve()}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc