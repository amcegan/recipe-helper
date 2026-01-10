# Recipe Helper

A modular, production-ready Python application that recommends recipes from photos of ingredients using Google Gemini.

## Setup Instructions

1. **Environment Configuration**:
   - Copy [.env.example](.env.example) to `.env`:
     ```bash
     cp .env.example .env
     ```
   - Set your `GEMINI_API_KEY` in the `.env` file.

2. **Get a Google AI Studio Key**:
   - Visit [Google AI Studio](https://aistudio.google.com/) to generate your API key.

3. **Production Security**:
   - **Important**: In a production environment, you should **not** use a `.env` file. Instead, manage secrets using:
     - CI/CD secret stores (e.g., GitHub Actions Secrets).
     - Cloud secret managers (e.g., Google Cloud Secret Manager, AWS Secrets Manager).
     - Directly injected environment variables.

4. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the Application**:
   ```bash
   streamlit run main.py
   ```

## Development

- **Run Tests**: `pytest tests/`
- **Architecture**: See [CLAUDE.md](CLAUDE.md) for detailed architecture and build instructions.
