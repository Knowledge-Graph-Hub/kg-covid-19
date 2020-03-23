from .utils import download_from_yaml

def download(yaml_file:str, output_dir:str):
    """
    download data files from list of URLs (default: download.yaml) into data directory
    (default: data/)
    """

    download_from_yaml(yaml_file=yaml_file, output_dir=output_dir)