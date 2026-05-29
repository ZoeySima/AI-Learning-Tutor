# AI Learning Tutor — Redefining Learning with AI

An AI-powered personalized learning assistant based on Claude, helping you quickly build "conceptual understanding" of unfamiliar domains.

## ✨ What's New in v0.2.0

**v0.2.0 brings 6 major improvements based on learning science principles**:

### 🎯 Smart Verification - No More "Fake Understanding"
- **Reasoning path validation**: Checks not just if your answer is correct, but if your thinking process is sound
- **Variant questions**: Generates alternative scenarios when you answer incorrectly to verify true understanding
- **Attempt tracking**: Records quiz history for each question

### 🔍 Fact-Checking - Ensuring Accuracy
- **Critical domain detection**: Finance, medical, legal topics automatically trigger dual-model verification
- **Auto-correction**: Regenerates content when factual errors are detected
- **Disclaimer injection**: Adds appropriate warnings for sensitive content

### 📋 Diagnostic Pretest - True Personalization
- **Prior knowledge assessment**: 3-5 diagnostic questions before generating the learning map
- **Adaptive depth**: Automatically adjusts chapter difficulty based on pretest results
- **Precise targeting**: AI analyzes your knowledge gaps and recommends focus areas

### 📊 Structured Notes - Building Learning Assets
- **Knowledge graphs**: Mermaid diagrams showing concept relationships
- **Collapsible sections**: Full content hidden by default, expandable on demand
- **Mastery tracking**: Visual progress bars + weak point analysis
- **Comparison tables**: Three perspectives side-by-side

### 🔄 Spaced Repetition - Combat Forgetting
- **Spiral review**: Automatically reviews chapters N-1 and N-3 before new content
- **Flashcard generation**: AI creates quick review questions
- **Scientific memory**: Based on Ebbinghaus forgetting curve

### 🎨 Visual Learning - Reduce Cognitive Load
- **ASCII diagrams**: Flow charts, tree structures, comparison tables
- **Progress visualization**: Chapter tree + completion status
- **Visual hierarchy**: Icons, colors, enhanced formatting

---

## Core Methodology

This tool implements a proven 4-step AI learning method:

1. **Map**: Generate a global learning map (chapter outline) to establish a framework first
2. **Learn**: Deep dive into each chapter with "three perspectives + real examples"
3. **Quiz**: Validate understanding with questions at the end of each chapter; pass to proceed
4. **Loop**: Repeat until all chapters are completed

## Why It Works

- **Personalized**: Diagnostic pretest + adjusts explanation based on your background
- **Active Validation**: Reasoning verification + variant questions expose blind spots
- **Structured Memory**: Build map first + spaced repetition for consolidation
- **Trust Foundation**: Fact-checking for critical domains ensures accuracy

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/ZoeySima/AI-Learning-Tutor.git
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
