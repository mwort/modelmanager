
.PHONY: update_docs clean

default:
	@echo Default target not defined. Check the Makefile for targets.

setup:
	virtualenv env
	source env/bin/activate
	pip install -r requirements_dev.txt
	python setup.py develop


clean:
	python setup.py clean
	rm -rf build/ dist/ *.egg-info
	find modelmanager -name \*.pyc -delete


# working dir should be clean (git)
update_docs:
	# build the docs
	cd docs && make clean && make html

	# commit and push
	git add -A
	git commit -m "building and pushing docs"
	git push origin master

	# switch branches and pull the data we want
	git checkout gh-pages
	rm -rf .
	touch .nojekyll
	git checkout master docs/build/html
	mv ./docs/build/html/* ./
	rm -rf ./docs
	git add -A
	git commit -m "publishing updated docs..."
	git push origin gh-pages

	# switch back
	git checkout master
