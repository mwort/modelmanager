
all: default plugins

default:
	python test_project.py -v

plugins:
	python test_browser.py -v
	python test_browser_multiproject.py -v
	python test_templates.py -v

clean:
	git clean -d -f -x ./*
