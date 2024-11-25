.PHONY: lint fix format export-dependencies clean

default: format

lint:
	ruff check
	mypy .

fix:
	ruff check --fix

format:
	ruff check --select I,F401 --fix
	ruff format

