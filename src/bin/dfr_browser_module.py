"""dfr_browser_module.

Python module to automatically set up and serve a dfr-browser instance. This is the basis for a command line tool `dfr-browser`, but also for a Python module that can be integrated into Lexos. The implementation is incomplete.

Usage:
browser = DfrBrowser("statefile.gz", "metadata.csv", "output_dir", "template.html")
browser.add_bibliography("bibliography.json")
browser.configure(title="My DFR Browser")
browser.configure(config_dict={"some_setting": True})
browser.serve(host='localhost', port=8000)

or from command line:

$ python dfr_browser_module.py statefile.gz metadata.csv output_dir template.html --host localhost --port 8000

Further modifications can be made to the configuration by editing the config.json file directly. Likewise, a bibliography file can be added by placing it in the data directory and updating the config.json file.
"""

import argparse
import http.server
import json
import os
import socketserver
import webbrowser
from pathlib import Path

from pydantic import BaseModel, Field


class DfrBrowser(BaseModel):
    state_file: Path | str = Field(..., description="Path to state file")
    metadata_file: Path | str = Field(..., description="Path to metadata file")
    output_dir: Path | str = Field(
        ..., description="Output directory for generated files"
    )
    template_dir: str | Path = Field(
        "dfr-browser", description="Path to HTML template directory"
    )

    def __init__(self, **data):
        super().__init__(**data)
        # Copy template file into output directory
        output_path = Path(self.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        template_path = Path(self.template_dir)
        if template_path.exists():
            dest_path = output_path / template_path.name
            with template_path.open("r") as src, dest_path.open("w") as dst:
                dst.write(src.read())

        # Copy the state file into the data directory
        state_path = Path(self.state_file)
        data_dir = output_path / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        if state_path.exists():
            dest_state_path = data_dir / state_path.name
            with state_path.open("r") as src, dest_state_path.open("w") as dst:
                dst.write(src.read())

        # Prepare the data
        self._prepare_data(dest_state_path)

    def _prepare_data(self, state_path: Path):
        """Prepare data for dfr-browser.

        This method would include logic to read the state file, parse it,
        and generate necessary data files for dfr-browser. This includes:

        Processes a MALLET topic-state.gz file and generates all necessary files for dfr-browser:
            - topic-keys.txt (topic words for browser)
            - doc-topic.txt (normalized proportions for browser)
            - topic_coords.csv (2D topic coordinates for browser)
            - tw.json (topic-words JSON for advanced features)
            - dt.zip (sparse doc-topic matrix for advanced features)
            - metadata.csv (basic document metadata if not exists)

        The main logic for processing the state file and generating the necessary files is in prepare_dfr_data.py.
        """
        # Implementation goes here
        pass

    def add_bibliography(self, bib_file: Path | str = None):
        """Add a bibliography file."""
        bib_path = Path(bib_file)
        if not bib_path.exists():
            metadata_path = Path(self.metadata_file)
            if metadata_path.exists():
                with metadata_path.open("r") as src, bib_path.open("w") as dst:
                    dst.write(src.read())
            else:
                raise FileNotFoundError(f"Bibliography file {bib_file} not found.")
        output_bib_path = Path(self.output_dir) / "data" / bib_path.name
        with bib_path.open("r") as src, output_bib_path.open("w") as dst:
            dst.write(src.read())
        self.configure(bibliography=str(output_bib_path))

    def configure(self, config_dict: dict = None, **kwargs):
        """Update configuration settings."""
        config_path = Path(self.output_dir) / "config.json"
        if config_path.exists():
            with config_path.open("r") as f:
                current_config = json.load(f)
        else:
            current_config = {}
        if config_dict:
            current_config.update(config_dict)
        current_config.update(kwargs)
        with open(config_path, "w") as f:
            json.dump(current_config, f, indent=2)

    def serve(self, host: str = "localhost", port: int = 8000):
        """Serve the dfr-browser locally."""
        os.chdir(self.output_dir)
        handler = http.server.SimpleHTTPRequestHandler
        with socketserver.TCPServer((host, port), handler) as httpd:
            print(f"Serving at http://{host}:{port}")
            webbrowser.open(f"http://{host}:{port}")
            httpd.serve_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Serve a dfr-browser instance.")
    parser.add_argument("state_file", type=str, help="Path to state file")
    parser.add_argument("metadata_file", type=str, help="Path to metadata file")
    parser.add_argument(
        "output_dir", type=str, help="Output directory for generated files"
    )
    parser.add_argument("template_dir", type=str, help="Path to HTML template file")
    parser.add_argument(
        "--host", type=str, default="localhost", help="Host to serve on"
    )
    parser.add_argument("--port", type=int, default=8000, help="Port to serve on")
    args = parser.parse_args()

    browser = DfrBrowser(
        state_file=args.state_file,
        metadata_file=args.metadata_file,
        output_dir=args.output_dir,
        template_dir=args.template_dir,
    )
    browser.serve(host=args.host, port=args.port)
