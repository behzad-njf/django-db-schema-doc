from io import StringIO

import pytest
from django.core.management import call_command


@pytest.mark.django_db
def test_generate_database_doc_to_stdout():
    buffer = StringIO()
    call_command(
        "generate_database_doc",
        to_stdout=True,
        title="Demo",
        stdout=buffer,
    )
    output = buffer.getvalue()
    assert "# Demo" in output
    assert "shop_product" in output
