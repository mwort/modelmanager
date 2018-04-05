PY = python
PLUGINS = browser browser_multiproject templates clone

all: default plugins

default:
	$(PY) test_project.py

plugins:
	for p in $(PLUGINS); do $(PY) test_$${p}.py ; done

clean:
	git clean -d -f -x ./*

coverage:
	$(MAKE) PY='coverage run -a' all
	coverage html -i --include=../modelmanager/*
	rm .coverage
