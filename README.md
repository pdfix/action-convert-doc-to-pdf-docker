# Word to PDF

A Docker image that converts Word documents (DOC, DOCX) and other word processing documents (ODT, RTF, ...) to accessible PDF (PDF/UA) using headless LibreOffice.

## Table of Contents

- [Word to PDF](#word-to-pdf)
  - [Getting started](#getting-started)
  - [Usage](#usage)
  - [Commands](#commands)
  - [Arguments](#arguments)
  - [Examples](#examples)
  - [Notes](#notes)
  - [Help \& support](#help--support)
  - [Licenses](#licenses)

## Getting started

You need Docker installed. The first run downloads the image and may take longer than later runs.

## Usage

Mount a folder into the container and run a subcommand:

```bash
docker run --rm -v "$(pwd)":/data -w /data pdfix/convert-doc-to-pdf:latest <command> [options]
```

## Commands

- `doc-to-pdf`: Convert a word processing document to PDF/UA

## Arguments

### `doc-to-pdf`

| Option | Required | Type / expected value | Description |
|---|:---:|---|---|
| `--input`, `-i` | yes | Path to an existing `.docx`, `.doc`, `.odt`, `.rtf`, ... file | Input document |
| `--output`, `-o` | yes | Path for the output `.pdf` file in an existing directory | Output PDF |
| `--standard` | no | One of: `ua1` (PDF/UA-1), `ua2` (PDF/UA-2), `ua1-a2b` (PDF/UA-1 and PDF/A-2b), `ua2-a4` (PDF/UA-2 and PDF/A-4) (default: `ua1`) | Standard of the output PDF |

## Examples

Convert a DOCX file to PDF/UA-1:

```bash
docker run --rm -v "$(pwd)":/data -w /data pdfix/convert-doc-to-pdf:latest doc-to-pdf -i /data/report.docx -o /data/report.pdf
```

Convert a DOC file to PDF/UA-1 and PDF/A-2b:

```bash
docker run --rm -v "$(pwd)":/data -w /data pdfix/convert-doc-to-pdf:latest doc-to-pdf -i /data/report.doc -o /data/report.pdf --standard ua1-a2b
```

## Notes

- The PDF is tagged from the document structure. Set the document title, use heading styles, add alternative text to images and a ScreenTip to hyperlinks to get a valid PDF/UA.
- PDF/UA-2 export in LibreOffice is new and some PDF/UA-2 rules may still fail validation. Use `ua1` for the most reliable result.
- Microsoft fonts are not included. Calibri, Cambria, Arial, Times New Roman and Courier New are replaced by metric-compatible fonts (Carlito, Caladea, Liberation), so the page layout is kept.
- Error codes are listed in `config.json` `errors` (print it with the `config` command).

## Help & support

To report an issue, contact `support@pdfix.net`.

## Licenses

- [LibreOffice](https://www.libreoffice.org/) (MPL-2.0)
- [Carlito](https://github.com/googlefonts/carlito), [Caladea](https://github.com/huertatipografica/Caladea) and [Liberation](https://github.com/liberationfonts) fonts (OFL-1.1)
- [DejaVu](https://dejavu-fonts.github.io/) fonts (Bitstream Vera Fonts License)
