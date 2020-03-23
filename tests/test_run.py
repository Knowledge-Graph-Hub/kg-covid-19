from kg_emerging_viruses import download, transform

def test_run():
    download("download.yaml", "data/raw")
    transform("data/raw", "data/transformed")