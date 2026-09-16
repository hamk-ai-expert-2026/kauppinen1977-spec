# Assignment #9: Product Description Generator CLI

Command-line application that analyzes one or more product images with OpenAI's multimodal Responses API and generates factual product marketing content.

The program produces:

- a product description
- short marketing slogans
- a separate list of image observations
- a separate list of user-provided facts

This separation is intentional: the model is instructed not to invent product specifications or marketing claims that are not visible in the images or supplied by the user.

## Requirements

- Python 3.10 or newer
- An OpenAI API key in the `OPENAI_API_KEY` environment variable

No Python packages need to be installed because the application uses only the Python standard library.

## Example

PowerShell:

```powershell
$env:OPENAI_API_KEY = "your_api_key_here"

python .\product_marketing.py `
  --images .\images\bottle_front.jpeg .\images\bottle_side.jpeg .\images\packaging.jpeg `
  --info "Portable drinking bottle. The packaging states 304 and 316 stainless steel. The product includes a carrying strap. Brand, capacity and temperature-retention time are unknown." `
  --language Finnish `
  --tone professional `
  --slogans 4 `
  --output .\output\bottle_marketing.txt
```

The result is printed to the terminal and, when `--output` is used, saved as a UTF-8 text file.

## Parameters

| Parameter | Required | Description |
| --- | --- | --- |
| `--images` | Yes | One or more JPEG, PNG or WebP product images. |
| `--info` | No | Additional factual product information. |
| `--language` | No | Output language. Default: `Finnish`. |
| `--tone` | No | Marketing tone. Default: `professional`. |
| `--slogans` | No | Number of slogans, from 1 to 10. Default: `4`. |
| `--output` | No | Text file where the result is saved. |

## Safety and accuracy

The application does not treat generated text as verified product data. Before publishing marketing content, verify all technical, material, safety and performance claims from an authoritative product source.
