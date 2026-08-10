APP_NAME=git-component
ENTRY=src/main.py

.PHONY: install build dist clean run test publish-check

install:
	pip install -r requirements-dev.txt

# Standalone single-file executable (no Python required on the target machine).
build:
	pyinstaller --onefile --name $(APP_NAME) $(ENTRY)

# PyPI-style sdist + wheel (installable via `pip install .` / `pip install <path-to-wheel>`).
dist:
	python -m build

clean:
	rm -rf build dist __pycache__ *.spec .pytest_cache *.egg-info src/*.egg-info

run:
	python $(ENTRY)

test:
	PYTHONPATH=src pytest

# Validates the built dist/ artifacts (metadata, README rendering, etc.)
# without uploading anything. Actually publishing (`twine upload dist/*`)
# is a one-way, externally-visible action and is intentionally not a
# make target — run it yourself once you're ready.
publish-check: dist
	twine check dist/*
