# Sample Python Project

This is a sample Python project created for testing the code development assistant's RAG and analysis capabilities.

## Features

- **Calculator Module**: Basic arithmetic operations with advanced functions
- **Data Processor**: File I/O and data manipulation utilities
- **Web Scraper**: Simple web scraping functionality
- **CLI Application**: Command-line interface using argparse
- **Configuration Management**: YAML and JSON configuration handling
- **Testing Suite**: Comprehensive unit tests

## Project Structure

```
sample_python_project/
├── README.md
├── requirements.txt
├── setup.py
├── main.py
├── config/
│   ├── config.yaml
│   └── settings.json
├── src/
│   ├── __init__.py
│   ├── calculator/
│   │   ├── __init__.py
│   │   ├── basic_ops.py
│   │   └── advanced_ops.py
│   ├── data_processing/
│   │   ├── __init__.py
│   │   ├── file_handler.py
│   │   └── data_analyzer.py
│   ├── web_scraper/
│   │   ├── __init__.py
│   │   └── scraper.py
│   └── utils/
│       ├── __init__.py
│       ├── config_loader.py
│       └── logger.py
├── tests/
│   ├── __init__.py
│   ├── test_calculator.py
│   ├── test_data_processing.py
│   └── test_web_scraper.py
└── data/
    ├── sample_data.csv
    └── test_data.json
```

## Usage

```bash
# Install dependencies
pip install -r requirements.txt

# Run the main application
python main.py --help

# Run tests
python -m pytest tests/
```

## Examples

This project demonstrates various Python patterns including:
- Object-oriented programming
- Functional programming
- Error handling
- File I/O operations
- API interactions
- Configuration management
- Logging
- Unit testing
