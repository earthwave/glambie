import sys
from unittest.mock import patch


from glambie.entrypoint import main


@patch.object(sys, 'argv', ["glambie", "-config", "/path/to/config"])
def test_main(capsys):
    main()
    stdout = str(capsys.readouterr())
    assert "/path/to/config" in stdout
