# v0.2.0 - Learning Science Improvements

## 🎓 Major Learning Science Improvements

This release implements 6 key optimizations based on learning science principles and user experience research.

---

## 🔥 P0 - Critical Improvements

### Quiz Reasoning Verification
- **Detect "fake understanding"**: Validates reasoning paths, not just final answers
- **Variant questions**: Generates alternative questions when user answers incorrectly
- **Attempt tracking**: Records how many tries each question took

**Example**: If you answer correctly but your reasoning is flawed, the system will catch it and ask you to explain your thinking.

### Fact-Checking for Critical Domains
- **Dual-model verification**: Uses Opus 4.7 to verify Sonnet 4.5 outputs
- **Auto-correction**: Regenerates content when factual errors detected
- **Critical domain detection**: Finance, medical, legal topics get extra scrutiny
- **Disclaimer injection**: Adds appropriate warnings for sensitive content

**Example**: When learning "金融衍生品", the system automatically fact-checks definitions, formulas, and examples.

---

## ⭐ P1 - High Priority

### Diagnostic Pretest
- **Prior knowledge assessment**: 3-5 questions before generating learning map
- **Adaptive depth**: Adjusts chapter difficulty based on pretest results
- **Smart analysis**: AI analyzes gaps and recommends focus areas

**Example**: Before teaching blockchain, asks if you understand "distributed systems" to gauge starting point.

### Structured Note Export
- **Knowledge graphs**: Mermaid diagrams showing concept relationships
- **Collapsible sections**: Full content hidden by default, expandable on demand
- **Mastery tracking**: Visual progress bars and weak point analysis
- **Table format**: Three perspectives in comparison tables
- **Quiz history**: Detailed feedback with reasoning validation status

**Example**: Exported notes include a visual graph of how concepts connect, plus a "weak points" section for targeted review.

---

## 🚀 P2 - Enhancements

### Spaced Repetition & Spiral Review
- **Interval-based recall**: Reviews chapters N-1 and N-3 before new content
- **Flashcard generation**: AI creates quick review questions
- **Combat forgetting curve**: Scientifically-proven retention strategy

**Example**: Before Chapter 4, you'll get flashcards reviewing Chapter 3 and Chapter 1.

### Visual Learning Aids
- **ASCII diagrams**: Flow charts, tree structures, comparison tables
- **Progress visualization**: Chapter tree with completion status
- **Enhanced display**: Visual hierarchy with icons and formatting

**Example**: Chapter outline now displays as a tree structure with progress bars.

---

## 📊 Technical Details

### New Features
- `LLMClient.verify_facts()` - Hallucination detection for critical domains
- `MapPhase._run_diagnostic_pretest()` - Prior knowledge assessment
- `LearnPhase._spiral_review()` - Spaced repetition implementation
- `QuizQuestion.reasoning_sound` - Track reasoning quality, not just correctness
- Structured markdown export with knowledge graphs

### Breaking Changes
- `evaluate_answer()` now returns `dict` instead of `tuple`
- `export_markdown()` output format significantly enhanced
- `generate_outline()` accepts `skip_pretest` parameter

### Files Changed
- 7 files modified, 771 lines added
- New: `DEPLOY.md`, `test_connection.py`

---

## 🎯 Why These Changes Matter

**Before v0.2.0**: Users could "guess correctly" and move on without understanding.

**After v0.2.0**: 
- Reasoning paths are validated
- Weak understanding triggers variant questions
- Spaced repetition ensures long-term retention
- Critical domains get fact-checked automatically

This transforms the tool from a "quiz system" into a true **learning companion** that ensures deep, lasting understanding.

---

## 📚 Methodology Source

These improvements are based on:
- **Learning Science**: Spaced repetition (Ebbinghaus), retrieval practice, metacognition
- **Product Testing**: Feedback from test PM on learning effectiveness
- **Cognitive Load Theory**: Visual aids, structured notes, progressive disclosure

---

## 🚀 Upgrade Instructions

```bash
cd ai-learning-tutor
git pull origin main
pip install -e . --force-reinstall
```

---

## 🙏 Credits

Methodology inspired by the WeChat article "Learning is Being Redefined by AI"

Built with [Anthropic Claude](https://www.anthropic.com/) API

---

**Full Changelog**: https://github.com/ZoeySima/AI-Learning-Tutor/compare/v0.1.0...v0.2.0
