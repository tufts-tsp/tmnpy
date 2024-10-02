from setuptools import setup

with open('requirements.txt') as f:
    requirements = f.read().splitlines()


setup(
    name="tmnpy",
    version="0.0.0",
    description="Threat Modeling Naturally in Python",
    author="Tufts Security & Privacy Lab",
    packages=[
        "tmnpy",
        "tmnpy.dsl",
        "tmnpy.kb",
        "tmnpy.engines",
        "tmnpy.util",
    ],
    package_data={
        "tmnpy.kb": [
            "reference_data/cwe.xml",
            "reference_data/capec.xml",
            "reference_data/asvs.xml",
            "reference_data/asvs_ref.json",
            "reference_data/threatlib.json",
            "reference_data/catalog.yaml",
        ]
    },
    install_requires=requirements
)
