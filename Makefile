VERSION=$(shell python -c "execfile('kiwi/__version__.py'); print '.'.join(map(str, version))")
PACKAGE=kiwi
DEBPACKAGE=python-kiwi
WEBDIR=/mondo/htdocs/async/projects/kiwi
TARBALL_DIR=/mondo/htdocs/stoq.com.br/download/sources

include common/async.mk

all:
	python setup.py build_ext -i

clean-docs:
	rm -fr doc/api
	rm -fr doc/howto

clean: clean-docs
	debclean
	rm -fr $(BUILDDIR)
	rm -f MANIFEST
	rm -fr kiwi/_kiwi.so

docs:
	make -s -C doc api howto

web: clean-docs docs
	cp -r doc/api ${WEBDIR}
	cp -r doc/howto ${WEBDIR}
	cp -r doc/howto.ps ${WEBDIR}
	gzip ${WEBDIR}/howto.ps
	cd ${WEBDIR} && tar cfz howto.tar.gz howto
	cd ${WEBDIR} && tar cfz api.tar.gz api

bdist:
	python setup.py -q bdist_wininst

release-tag:
	svn cp -m "Tag $(VERSION)" . svn+ssh://async.com.br/pub/kiwi/tags/$(VERSION)

upload-release: sdist bdist
	scp dist/$(TARBALL) johan@gnome.org:
	ssh gnome.org install-module $(TARBALL)
	scp dist/kiwi-$(VERSION).win32.exe gnome.org:/ftp/pub/GNOME/binaries/win32/kiwi/

.PHONY: bdist upload-release
