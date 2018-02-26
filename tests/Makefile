PY = python
PLUGINS = browser browser_multiproject templates clone

all: default plugins

default:
	$(PY) test_project.py -v

plugins:
	for p in $(PLUGINS); do $(PY) test_$${p}.py ; done

clean:
	git clean -d -f -x ./*

coverage: all
	coverage html -i --include=../modelmanager/*
