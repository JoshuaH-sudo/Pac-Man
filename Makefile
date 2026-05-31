.PHONY: install run debug clean lint lint-strict test

# Using UV_SKIP_WHEEL_FILENAME_CHECK=1 to work around a known issue with uv and certain wheel filenames.
UV = UV_SKIP_WHEEL_FILENAME_CHECK=1 uv

install:
	$(UV) sync --all-groups

run:
	$(UV) run python pac-man.py config.example.json

debug:
	$(UV) run python -m pdb pac-man.py config.example.json

clean:
	find . -type d \( -name '__pycache__' -o -name '.mypy_cache' -o -name '.pytest_cache' \) -prune -exec rm -rf {} +
	find . -type f \( -name '*.pyc' -o -name '*.pyo' \) -delete

lint:
	$(UV) run flake8 .
	$(UV) run mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	$(UV) run flake8 .
	$(UV) run mypy . --strict

test:
	$(UV) run pytest -q
