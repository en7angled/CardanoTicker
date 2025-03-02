from setuptools import find_packages, setup

setup(
    name="cardano_ticker",
    version="0.1.0",
    description="A customizable Cardano Ticker with e-ink and LCD display options.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Andrei Georgescu",
    author_email="andrei.georgescoo@yahoo.com",
    url="https://github.com/en7angled/CardanoTicker",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,  # Required for non-code files
    package_data={
        "cardano_ticker": ["data/**/*"],  # Adjust the path to match your project structure
    },
    install_requires=[
        "requests>=2.25.0,<=3.0.0",
        "matplotlib>=3.4.0,<=3.6.3",
        "numpy>=1.26.3,<2",
        "pandas<=2.2.0",
        "Pillow>=9.5.0,<=11.1.0",
        "blockfrost-python>=0.6.0",
        "flask>=2.1.0",
        "werkzeug>=2.2.3",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9, <=3.11.2",
    entry_points={
        "console_scripts": [
            "cardano-ticker-provider=cardano_ticker.dashboards.dashboard_provider:main",
            "cardano-ticker-controller=cardano_ticker.dashboards.dashboard_controller:controller",
        ],
    },
)
