# AI Learning Tutor — Redefining Learning with AI

An AI-powered personalized learning assistant based on Claude, helping you quickly build "conceptual understanding" of unfamiliar domains.

## Core Methodology

This tool implements a proven 4-step AI learning method:

1. **Map**: Generate a global learning map (chapter outline) to establish a framework first
2. **Learn**: Deep dive into each chapter with "three perspectives + real examples"
3. **Quiz**: Validate understanding with questions at the end of each chapter; pass to proceed
4. **Loop**: Repeat until all chapters are completed

## Why It Works

- **Personalized**: Adjusts explanation granularity based on your background
- **Active Validation**: Not passive reading, but exposing blind spots through quizzes
- **Structured Memory**: Build the map first, then fill in details—new knowledge has hooks

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/ai-learning-tutor.git
cd ai-learning-tutor

# Install dependencies
pip install -r requirements.txt

# Or install with pip (development mode)
pip install -e .
```

### Configure API Key

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Start Learning

```bash
# Start a new learning session
ai-tutor start "Blockchain Fundamentals"

# Resume an existing session
ai-tutor resume 20260527-blockchain

# List all sessions
ai-tutor list

# Export learning notes
ai-tutor export 20260527-blockchain -o notes.md
```

## Use Cases

- Quickly understand unfamiliar industries (new projects, career transitions)
- Learn new tech stacks (programming languages, frameworks, tools)
- Supplement domain knowledge (finance, law, medical concepts)
- Exam preparation (build knowledge frameworks)

## Project Structure

```
ai-learning-tutor/
├── ai_tutor/
│   ├── __init__.py
│   ├── __main__.py        # CLI entry point
│   ├── cli.py             # Command-line interface
│   ├── core.py            # 4-step learning engine
│   ├── llm.py             # LLM client wrapper
│   ├── state.py           # State management
│   └── prompts.py         # Prompt templates
├── examples/              # Example sessions
├── tests/                 # Tests
├── README.md
├── README_EN.md
├── LICENSE
├── pyproject.toml
└── requirements.txt
```

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Code formatting
black ai_tutor/
ruff check ai_tutor/
```

## Methodology Source

The methodology of this tool comes from a practical article about "Learning with AI". The core idea is:

> As AI becomes more powerful, the requirements for humans actually increase. What decreases is the execution-level requirement, but the conceptual-level requirement is raised. You need to know what something is, why it exists, and its relationship with other things.

See [docs/methodology.md](docs/methodology.md) for details.

## License

MIT License - see [LICENSE](LICENSE)

## Contributing

Issues and Pull Requests are welcome!

## Acknowledgments

- Methodology inspired by the WeChat article "Learning is Being Redefined by AI"
- Built on [Anthropic Claude](https://www.anthropic.com/) API
- CLI interface powered by [Rich](https://github.com/Textualize/rich)
