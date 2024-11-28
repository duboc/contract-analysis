# Contract Analysis Application

A powerful tool for analyzing and extracting information from contracts using advanced language models and natural language processing techniques.

## Features

- Contract text extraction from PDF documents
- Intelligent contract analysis and information extraction
- Question-answering capabilities about contract contents
- Support for multiple document formats
- Clean and intuitive user interface

## Prerequisites

- Python 3.8 or higher
- Node.js and npm (for the frontend)
- Required Python packages (see `requirements.txt`)

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd contract-analysis
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Install frontend dependencies:
```bash
cd frontend
npm install
```

## Usage

1. Start the backend server:
```bash
python app.py
```

2. Access the application through your web browser at `http://localhost:5000`

3. Upload a contract document and start analyzing!

## Project Structure

```
contract-analysis/
├── app.py              # Main Flask application
├── frontend/          # Frontend React application
├── static/           # Static assets
├── templates/        # HTML templates
└── requirements.txt  # Python dependencies
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the Apache License - see the LICENSE file for details. 