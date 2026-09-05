import os
import json
import platform
import shutil
import subprocess
import sys
import tempfile
from dotenv import load_dotenv
from IPython.display import Markdown, display, update_display
from pathlib import Path
from scraper import fetch_website_links, fetch_website_contents
from openai import OpenAI
from brochure_pdf import save_brochure_pdf
import gradio as gr

load_dotenv(override=True)
api_key = os.getenv('GROQ_API_KEY')
groq = OpenAI(base_url="https://api.groq.com/openai/v1",api_key=api_key)
MODEL = "openai/gpt-oss-20b"


# LLM call 1 : select relevant links
link_system_prompt = """
You are provided with a list of links found on a webpage.
You are able to decide which of the links would be most relevant to include in a brochure about the company,
such as links to an About page, or a Company page, or Careers/Jobs pages.
You should respond in JSON as in this example:

{
    "links": [
        {"type": "about page", "url": "https://full.url/goes/here/about"},
        {"type": "careers page", "url": "https://another.full.url/careers"}
    ]
}
"""

def get_links_user_prompt(url):
    user_prompt = f"""
        Here is the list of links on the website {url} -
        Please decide which of these are relevant web links for a brochure about the company, 
        respond with the full https URL in JSON format.
        Do not include Terms of Service, Privacy, email links.

        Links (some might be relative links):

        """
    links = fetch_website_links(url)
    user_prompt += "\n".join(links)
    return user_prompt


def select_relevant_links(url):
    print(f"Selecting relevant links for {url} by calling {MODEL}")
    response = groq.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": link_system_prompt},
            {"role": "user", "content": get_links_user_prompt(url)}
        ],
        response_format={"type": "json_object"}
    )
    result = response.choices[0].message.content
    links =json.loads(result)
    return links
# End of LLM call 1


# LLM call 2 : Generate the brochure with help of first LLM call's relevant links
def fetch_page_and_all_relevant_links(url):
    contents = fetch_website_contents(url)
    relevant_links = select_relevant_links(url) # returned with LLM reasoning
    result = f"## Landing Page:\n\n{contents}\n## Relevant Links:\n"
    for link in relevant_links['links']:
        result += f"\n\n### Link: {link['type']}\n"
        #print(f'check: {link["url"]}')
        result += fetch_website_contents(link["url"]) # add the contents from the selected relevant links from the page
    return result

brochure_system_prompt = """
You are an assistant that analyzes the contents of several relevant pages from a company website
and creates a short brochure about the company for prospective customers, investors and recruits.
Respond in markdown without code blocks.
Include details of company culture, customers and careers/jobs if you have the information.
"""

def get_brochure_user_prompt(company_name, url):
    user_prompt = f"""
You are looking at a company called: {company_name}
Here are the contents of its landing page and other relevant pages;
use this information to build a short brochure of the company in markdown without code blocks.\n\n
"""
    user_prompt += fetch_page_and_all_relevant_links(url) # user prompt stiched from previous LLM call
    user_prompt = user_prompt[:5_000] # Truncate if more than 5,000 characters
    return user_prompt

def create_brochure(company_name, url, save_folder=""):
    response = groq.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": brochure_system_prompt},
            {"role": "user", "content": get_brochure_user_prompt(company_name, url)}
        ],
        stream=True
    )
    result = ""
    for chunk in response:
        result += chunk.choices[0].delta.content or ""
        yield result, None

    output_dir = Path(save_folder).expanduser() if save_folder and save_folder.strip() else None
    pdf_path = save_brochure_pdf(result, company_name, output_dir=output_dir)
    # Gradio's File component can only serve files from cwd, temp, or allowed_paths.
    download_copy = Path(tempfile.gettempdir()) / pdf_path.name
    shutil.copy2(pdf_path, download_copy)
    yield result, str(download_copy)
# End of LLM call 2


def choose_save_folder():
    """Open a native folder picker and return the selected path."""
    pickers = {
        "Darwin": ["osascript", "-e", 'POSIX path of (choose folder)'],
        "Windows": [
            "powershell", "-NoProfile", "-Command",
            "Add-Type -AssemblyName System.Windows.Forms; "
            "$d = New-Object System.Windows.Forms.FolderBrowserDialog; "
            "if ($d.ShowDialog() -eq 'OK') { $d.SelectedPath }",
        ],
    }
    cmd = pickers.get(platform.system(), [
        sys.executable, "-c",
        "import tkinter as tk; from tkinter import filedialog; "
        "r = tk.Tk(); r.withdraw(); r.attributes('-topmost', True); "
        "print(filedialog.askdirectory(), end=''); r.destroy()",
    ])
    try:
        folder = subprocess.run(cmd, capture_output=True, text=True).stdout.strip()
    except OSError:
        folder = ""
    return folder or gr.update()


with gr.Blocks(title="Company Brochure Generator") as view:
    gr.Markdown(
        "# Company Brochure Generator\n"
        "Enter a company name and URL. Choose a save folder, or leave it unset to use `brochures/`."
    )
    with gr.Row():
        company_name = gr.Textbox(label="Company Name", lines=7)
        url = gr.Textbox(label="Company URL", lines=7)
    with gr.Row():
        choose_folder_btn = gr.Button("Choose save folder")
        save_folder = gr.Textbox(
            label="Selected folder",
            interactive=False,
            placeholder="No folder selected — PDF will be saved under brochures/",
        )
    generate_btn = gr.Button("Generate Brochure", variant="primary")
    message_output = gr.Markdown(label="Response:")
    pdf_output = gr.File(label="Download PDF")
    choose_folder_btn.click(choose_save_folder, outputs=save_folder)
    generate_btn.click(create_brochure, [company_name, url, save_folder], [message_output, pdf_output])

view.launch(inbrowser=True)