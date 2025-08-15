def get_glambie_bucket_name(glambie_version: int) -> str:
    if glambie_version == 1:
        return "glambie-submissions"
    elif glambie_version == 2:
        return "glambie2-submissions"
    else:
        raise ValueError(f"Invalid glambie_version: {glambie_version}")
