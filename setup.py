from setuptools import setup, find_packages

setup(
    name="momentum-telegram-bot",
    version="0.0.1",
    packages=find_packages(),
    install_requires=[
        "pyTelegramBotAPI",
        "python-dotenv",
        "requests",
        "json",
        "pandas",
        "yfinance",
        "DateTime",
        "matplotlib",
        "scikit-learn",
        "numpy",
        "mysql-connector-python"
    ],
    include_package_data=True,
)