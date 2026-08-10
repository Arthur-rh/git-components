APP_NAME=git-component
ENTRY=src/main.py

build:
	pyinstaller --onefile --name $(APP_NAME) $(ENTRY)

clean:
	rm -rf build dist __pycache__ *.spec

run:
	python $(ENTRY)