
def strip_python_tags(yaml_string: str):
    """
    Strips the python tags from a yaml

    Parameters
    ----------
    yaml_string : str
        yaml string

    Returns
    -------
    _type_
        stripped yaml string
    """
    result = []
    for line in yaml_string.splitlines():
        idx = line.find("!!python/")
        if idx > -1:
            line = line[:idx]
        result.append(line)
    return '\n'.join(result)
