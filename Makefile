
.PHONY: update_docs clean

default:
	@echo Default target not defined. Check the Makefile for targets.

setup:
	virtualenv env
	source env/bin/activate
	pip install -r requirements_dev.txt
	pip install -e .


clean:
	python setup.py clean
	rm -rf build/ dist/ *.egg-info
	find modelmanager -name \*.pyc -delete

version:
	@prev=`python -c 'import modelmanager; print(modelmanager.__version__)'` ;\
	echo Old version: $$prev ;\
	read -p "New version number (CHANGELOG.md updated? <ctrl-c> if not): " new; \
	for f in `grep -rlI $$prev modelmanager README.md docs`; do \
		sed -i.backup "s/$$prev/$$new/g" $$f ; rm -r $$f.backup ; done ; \
	git commit -a -m "Bumped version $$prev > $$new ." ; \
	git tag $$new

release:
	python setup.py sdist
	git push
	git push --tags
	twine upload dist/*


docs:
	sphinx-apidoc --ext-viewcode --ext-autodoc -d 2 -f -o docs/api modelmanager/
	cd docs && make clean && make html


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
