import bleach
import markdown


def markdown_to_html(text):
    """Converts the given text from markdown to html.

    Note that this function will only sanitize the html after conversion. This means that html from the input text
    will not be escaped unless it is deemed unsafe.
    """
    text = markdown.markdown(text)

    allowed_tags = bleach.ALLOWED_TAGS + ['h1', 'h2', 'h3', 'p']
    text = bleach.clean(text, allowed_tags)

    return text
