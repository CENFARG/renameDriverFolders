# AI Agent Guidelines for renameDriverFolders

## Build & Test Commands
- **Install Dependencies:** `pip install -r requirements.txt`
- **Run Application:** `python main.py`
- **Run All Tests:** `pytest`
- **Run Single Test:** `pytest tests/test_integration.py::test_specific_case`
- **Linting:** Follow PEP 8 standards.

## Code Style & Standards
- **Architecture:** Adhere to `.standards_cenf/AGENT_CODING_STANDARDS.md` (Sense-Think-Act pattern).
- **Imports:** Absolute imports preferred. Use `core` modules (`config_manager`, `logger_manager`) instead of reinventing.
- **Configuration:** Manage settings via `config.json` using `core.config_manager`. Avoid hardcoded paths.
- **Logging:** Use `core.logger_manager`. Maintain `logs/justifications.log` (reasoning) and `logs/backlog.log` (technical).
- **Error Handling:** Use `core.error_handler` to manage exceptions gracefully.
- **Memory Bank:** Update `memory-bank/` documentation when architectural changes occur.
- **Naming:** snake_case for variables/functions, PascalCase for classes. CONSTANTS_UPPERCASE.
- **Deployment:** Refer to `Dockerfile` or `deployment/` scripts for release procedures.
