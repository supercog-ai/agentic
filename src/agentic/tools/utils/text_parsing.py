import re


def format_sources(content: str):
    """
    Removes embedded Markdown links and concatenates a 'Sources' section with deduplicated URLs.
    """
    # Pattern to match Markdown links: [text](url)
    pattern = re.compile(r'\(\[([^\]]+)\]\((https?://[^\)]+)\)\)')
    sources = []

    def replacer(match):
        url = match.group(2)

        # The string to replace the embedded links with
        replacement = f""

        if url in sources:
            return replacement
        else:
            sources.append(url)

        return replacement

    formatted_content = pattern.sub(replacer, content)
    sourcesString = "Sources: " + '\n'.join(sources)

    result = formatted_content + '\n' + sourcesString
    return result

