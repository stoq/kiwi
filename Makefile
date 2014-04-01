VERSION=$(shell python -c "execfile('kiwi/__version__.py'); print '.'.join(map(str, version))")
PACKAGE=kiwi
WEBDIR=/mondo/htdocs/async.com.br/www/projects/kiwi

all:
	python setup.py build_ext -i

clean-docs:
	rm -fr doc/api
	rm -fr doc/howto

clean:
	rm -fr build
	rm -f MANIFEST

docs:
	make -s -C doc api howto

apidocs:
	make -C docs/api pickle html devhelp

upload-apidocs:
	scp -r docs/api/_build/html anthem:/var/www/stoq.com.br/doc/api/kiwi

web: clean-docs docs
	cp -r doc/api ${WEBDIR}
	cp -r doc/howto ${WEBDIR}
	cp -r doc/howto.ps ${WEBDIR}
	gzip ${WEBDIR}/howto.ps
	cd ${WEBDIR} && tar cfz howto.tar.gz howto
	cd ${WEBDIR} && tar cfz api.tar.gz api

check: check-source-all
	# FIXME: Move from trial to nosetests
	trial tests

include utils/utils.mk
.PHONY: all clean-docs clean docs apidocs upload-apidocs web check
