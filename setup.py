from setuptools import setup, find_packages

setup(
    name="geoscope",
    version="1.0.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "typer[all]",
        "rich",
        "sqlalchemy",
        "requests",
        "pandas",
        "folium",
        "python-dotenv",
        "newspaper3k",
        "feedparser",
        "duckduckgo-search==5.3.0",
        "beautifulsoup4",
        "lxml",
        "pystac-client",
        "geopy",
        "python-dateutil"
    ],
    entry_points={
        "console_scripts": [
            "geoscope=geoscope.cli:app",
        ],
    },
)