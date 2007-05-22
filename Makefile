WEBDIR=/mondo/htdocs/async/projects/kiwi
VERSION=$(shell python -c "execfile('kiwi/__version__.py'); print '.'.join(map(str, version))")
BUILDDIR=tmp
PACKAGE=kiwi
TARBALL=$(PACKAGE)-$(VERSION).tar.gz
DEBVERSION=$(shell dpkg-parsechangelog -ldebian/changelog|egrep ^Version|cut -d\  -f2)
DLDIR=/mondo/htdocs/stoq.com.br/download/ubuntu
TESTDLDIR=/mondo/htdocs/stoq.com.br/download/test
TARBALL_DIR=/mondo/htdocs/stoq.com.br/download/sources

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

sdist: docs
	bin/kiwi-i18n -c
	python setup.py -q sdist

bdist:
	python setup.py -q bdist_wininst

deb: sdist
	rm -fr $(BUILDDIR)
	mkdir $(BUILDDIR)
	cd $(BUILDDIR) && tar xfz ../dist/$(TARBALL)
	cd $(BUILDDIR)/kiwi-$(VERSION) && debuild -S
	rm -fr $(BUILDDIR)/kiwi-$(VERSION)
	mv $(BUILDDIR)/* dist
	rm -fr $(BUILDDIR)

rpm:
	rpmbuild --define="_sourcedir `pwd`/dist" \
	         --define="_srcrpmdir `pwd`/dist" \
	         --define="_rpmdir `pwd`/dist" \
	         --define="_builddir `pwd`/build" \
                 -ba kiwi.spec
	mv dist/noarch/* dist
	rm -fr dist/noarch

release-deb:
	debchange -v $(VERSION)-1 "New release"

release: clean release-deb sdist bdist deb

release-tag:
	svn cp -m "Tag $(VERSION)" . svn+ssh://svn.async.com.br/pub/kiwi/tags/$(VERSION)

upload-release: sdist bdist
	scp dist/$(TARBALL) gnome.org:
	ssh gnome.org install-module $(TARBALL)
	scp dist/kiwi-$(VERSION).win32.exe gnome.org:/ftp/pub/GNOME/binaries/win32/kiwi/

upload:
	cp dist/$(PACKAGE)*_$(DEBVERSION)*.deb $(DLDIR)
	for suffix in "gz" "dsc" "build" "changes"; do \
	  cp dist/$(PACKAGE)_$(DEBVERSION)*."$$suffix" $(DLDIR); \
	done
	/mondo/local/bin/update-apt-directory $(DLDIR)

test-upload:
	cp dist/$(PACKAGE)*_$(DEBVERSION)*.deb $(TESTDLDIR)/ubuntu
	cp dist/python-kiwi-*$(VERSION)*.rpm $(TESTDLDIR)/fedora
	for suffix in "gz" "dsc" "build" "changes"; do \
	  cp dist/$(PACKAGE)_$(DEBVERSION)*."$$suffix" $(TESTDLDIR)/ubuntu; \
	done
	/mondo/local/bin/update-apt-directory $(TESTDLDIR)/ubuntu


tags:
	find -name \*.py|xargs ctags

TAGS:
	find -name \*.py|xargs etags

nightly:
	/mondo/local/bin/build-svn-deb

.PHONY: docs web sdist bdist release deb upload upload-release
