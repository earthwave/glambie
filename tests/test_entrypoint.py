import sys
from unittest.mock import patch

from glambie.entrypoint import main


@patch.object(sys, 'argv', ["glambie", "tests/test_data/configs/test_config_empty.yaml", "-q"])
def test_main(capsys):
    main()
    stdout = str(capsys.readouterr())
    assert "GlaMBIE" in stdout
