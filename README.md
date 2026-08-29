# Company Sales Brochure Generator

Give it a company name and a website URL, and it scrapes the site, asks an
LLM to figure out which pages actually matter (About, Careers, etc.),
feeds all that content back into the LLM to write a short marketing
brochure, and finally renders that brochure as a styled, branded PDF.

## How it works

The pipeline (implemented in `playground.ipynb`, backed by `scraper.py`
and `brochure_pdf.py`) runs in five steps:

1. **Scrape the landing page.** `fetch_website_contents()` downloads the
   URL, strips out scripts/styles/images, and returns the page title plus
   clean visible text. `fetch_website_links()` pulls every absolute
   `http(s)` link off the page.
2. **Let the LLM pick the relevant links.** All links found in step 1 are
   sent to the model with a prompt asking it to return only the pages
   worth including in a brochure (About, Company, Careers, etc.) as JSON,
   skipping Terms/Privacy/email links.
3. **Scrape those relevant pages too.** Each selected link is fetched the
   same way as the landing page, and everything is stitched together into
   one combined document (capped at 5,000 characters before it's sent to
   the model).
4. **Generate the brochure copy.** The combined page content is sent to
   the LLM with a system prompt asking for a short markdown brochure
   covering company culture, customers, and careers. A commented-out
   alternate prompt in the notebook produces a more humorous tone instead.
5. **Render it as a PDF.** `save_brochure_pdf()` parses that markdown
   (headings, bullets, bold/italic, horizontal rules) and lays it out
   into a navy/gold-branded A4 PDF using `fpdf2`, saved under
   `brochures/<company-slug>-brochure.pdf`.

There's also a `stream_brochure()` variant that streams the model's
response token-by-token into a live-updating Markdown cell, for a
typewriter effect in the notebook.

## Project structure

```
.
├── playground.ipynb   # Orchestrates the whole pipeline, cell by cell
├── scraper.py          # fetch_website_links / fetch_website_contents
├── brochure_pdf.py      # Markdown → branded PDF renderer
├── pyproject.toml       # Project dependencies
├── uv.lock              # Locked dependency versions
└── brochures/            # Output folder (created automatically)
```

## Setup

1. **Install [uv](https://docs.astral.sh/uv/)** (Python package/dependency
   manager), if you don't have it already:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
2. **Clone the project and install dependencies.** `uv sync` reads
   `pyproject.toml` / `uv.lock` and creates a `.venv` with everything
   pinned:
   ```bash
   git clone <this-repo-url>
   cd Company-Sales-Broshure-Generator
   uv sync
   ```
3. **Get an API key.** The notebook currently calls an LLM through
   [Groq's](https://console.groq.com) OpenAI-compatible endpoint, using
   model `openai/gpt-oss-20b`. Sign up on Groq and generate an API key
   (it starts with `gsk_`).
4. **Create a `.env` file** in the project root with your key:
   ```
   GROQ_API_KEY=gsk_your_key_here
   ```
   (The dependencies also include `anthropic`, `openai`, and
   `google-generativeai`, so you can swap in Claude, OpenAI, or Gemini
   instead — just point the client and model name in the notebook at
   whichever provider you'd rather use, and add the matching key to
   `.env`.)
5. **Register the kernel and launch Jupyter:**
   ```bash
   uv run python -m ipykernel install --user --name company-brochure
   uv run jupyter notebook
   ```
   Open `playground.ipynb` and select the kernel you just registered.

## Usage

Run the notebook cells top to bottom, then call:

```python
create_brochure("Your Company", "https://yourcompany.com")
```

This prints the generated markdown inline in the notebook and saves a
PDF to `brochures/your-company-brochure.pdf`. For a live typewriter-style
preview instead, use:

```python
stream_brochure("Your Company", "https://yourcompany.com")
```

## Notes

- Page content is truncated to 5,000 characters before being sent to the
  LLM, to keep prompts small — very content-heavy sites will be
  summarized from a partial view.
- The PDF renderer falls back through a list of common system font paths
  (Arial / DejaVu Sans); on a fresh machine you may need to install one
  of these fonts, and some special characters (like `₹` or non-standard
  dashes) may not render if the chosen font lacks that glyph.
- The scraper only follows links present in the raw HTML — pages that
  are loaded client-side via JavaScript won't be picked up.