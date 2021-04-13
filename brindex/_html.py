"""Basic HTML construction for showing lists according to PEP 503."""


def make_html_list_page(elements, prefix=""):
    return """
<!DOCTYPE html>
<html>
  <body>
    {}
  </body>
</html>
    """.format("<br>".join(
        _make_list_element(elt, prefix) for elt in elements
    ))


def _make_list_element(elt, prefix=""):
    return f'<a href="{prefix}/{elt}">{elt}</a>'
