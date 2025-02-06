# Contract Analysis Application

A powerful tool for analyzing contracts against regulatory requirements using Google's Vertex AI and Streamlit. The application helps identify potential risks and suggests improvements based on regulatory guidelines.

## Features

- PDF contract analysis with page-by-page tracking
- Regulatory compliance checking
- Risk level assessment (High/Medium)
- Suggested improvements for risky clauses
- Reference document management
- Interactive PDF viewing
- API interaction logging
- Clean and intuitive Streamlit interface

## Prerequisites

- Python 3.8 or higher
- Google Cloud Platform account with Vertex AI API enabled
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

3. Set up environment variables:
   - Copy `.env.example` to create your own `.env` file:
   ```bash
   cp .env.example .env
   ```
   - Edit `.env` with your configuration:
   ```
   VERTEX_PROJECT_ID=your-project-id-here
   VERTEX_REGION=your-region-here
   ```

## Usage

1. Place your contract PDFs in the `data/` directory
2. Place reference regulatory documents in the `docs/` directory
3. Start the Streamlit application:
```bash
streamlit run app.py
```
4. Access the application through your web browser at the URL shown in the terminal (typically `http://localhost:8501`)

## Project Structure

```
contract-analysis/
├── app.py                    # Main Streamlit application
├── services/                 # Service modules
│   └── vertex_service.py     # Vertex AI integration
├── utils/                    # Utility functions
│   └── logging_utils.py      # Logging utilities
├── prompts/                  # Analysis prompts
│   ├── regulatory_analysis.md
│   └── reference_analysis.md
├── data/                     # Contract documents
├── docs/                     # Regulatory reference documents
├── .env.example             # Environment variables template
└── requirements.txt         # Python dependencies
```

## Environment Variables

- `VERTEX_PROJECT_ID`: Your Google Cloud Project ID
- `VERTEX_REGION`: The region for Vertex AI services (e.g., us-central1)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the Apache License - see the LICENSE file for details. 