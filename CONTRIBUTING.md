# Contributing to REREAL - Spitit

Thank you for your interest in contributing! Here's how you can help.

## 🐛 Reporting Bugs

1. Check [existing issues](https://github.com/VIKAS-REREAL/REREAL-Spitit/issues) first
2. Use the [bug report template](.github/ISSUE_TEMPLATE/bug_report.md)
3. Include your Windows version, app version, and steps to reproduce

## 💡 Suggesting Features

1. Check [existing feature requests](https://github.com/VIKAS-REREAL/REREAL-Spitit/issues?q=label%3Aenhancement)
2. Use the [feature request template](.github/ISSUE_TEMPLATE/feature_request.md)

## 🔧 Development Setup

```powershell
# Clone the repo
git clone https://github.com/VIKAS-REREAL/REREAL-Spitit.git
cd REREAL-Spitit

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run the app
python src/main.py
```

## 📝 Code Style

- Follow PEP 8
- Use type hints where practical
- Add docstrings to all public functions and classes
- Keep imports sorted (stdlib → third-party → local)

## 🔀 Pull Requests

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Make your changes
4. Test thoroughly on Windows 10/11
5. Submit a pull request

## 📋 Guidelines

- All UI code must run on the main thread
- Use `root.after(0, fn)` for cross-thread UI updates
- Import heavy modules lazily (inside functions)
- Test: app must not crash if no microphone is connected
- Test: app must not crash if Groq API is unreachable

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.
