from pathlib import Path

TEXT_EXTENSIONS = {
    ".html",
    ".css",
    ".js",
    ".json",
    ".xml",
    ".txt",
    ".md",
    ".yml",
    ".yaml",
}


def on_post_build(config, **kwargs):
    site_dir = Path(config["site_dir"])

    for path in site_dir.rglob("*"):
        if not path.is_file():
            continue

        if path.suffix.lower() not in TEXT_EXTENSIONS:
            continue

        content = path.read_text(encoding="utf-8")

        # Normalize CRLF or old Mac CR to LF
        content = content.replace("\r\n", "\n").replace("\r", "\n")

        path.write_text(content, encoding="utf-8", newline="\n")
