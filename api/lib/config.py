import os


def is_prod():

    if os.environ.get("ENVIRONMENT") == "prod":
        return True
    assert os.environ.get("ENVIRONMENT") == "dev"
    return False


def is_dev():
    if os.environ.get("ENVIRONMENT") == "dev":
        return True
    assert os.environ.get("ENVIRONMENT") == "prod"
    return False
