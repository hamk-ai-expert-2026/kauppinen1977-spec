# Assignment 7: Image to Text to Image

This project analyses an input image with a vision-capable language model and uses the generated textual description as a prompt for an image-generation model.

## Models

- Vision: gpt-5.6-luna
- Image generation: gpt-image-2

## Usage

```powershell
python image_to_text_to_image.py `
  --input "Koira_pehmolelu.jpeg" `
  --output "output/generated.png"
