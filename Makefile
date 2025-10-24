format:
	uv run ruff check --select I --fix .
	uv run ruff format .

run_benchmark:
	uv run python main.py
