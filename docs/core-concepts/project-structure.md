# Project Structure

An Agentic project has the following structure:

```
<root>/
    pyproject.toml
    agents/
        agent1.py
        agent1.prompts.yaml
        agent2.py
    tools/
        weather_tool.py
        news_tool.py
        tests/
            test_weather_tool.py
            test_news_tool.py
    indexes/
        personal.rag.sqlite
        dev.rag.sqlite
    evals/
        agent1.eval
        agent2.eval
    runtime/
        agent_runs.db
```
