import sys
from unittest.mock import patch


from python_template.example_entrypoint import main


@patch.object(sys, 'argv', ["python_template", "-a", "4", "-b", "5"])
def test_main(capsys):
    main()
    stdout = str(capsys.readouterr())
    assert "Worse Calculator Output" in stdout
    assert "9" in stdout
