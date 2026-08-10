APP_NAME=git-component
ENTRY=src/main.py

.PHONY: install build clean run test

install:
	pip install -r requirements-dev.txt

build:
	pyinstaller --onefile --name $(APP_NAME) $(ENTRY)

clean:
	rm -rf build dist __pycache__ *.spec .pytest_cache

run:
	python $(ENTRY)

test:
	PYTHONPATH=src pytest
