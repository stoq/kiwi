WEBDIR=/mondo/htdocs/async/projects/kiwi
VERSION=$(shell python -c "execfile('kiwi/__version__.py'); print '.'.join(map(str, version))")
BUILDDIR=tmp
PACKAGE=kiwi
TARBALL=$(PACKAGE)-$(VERSION).tar.gz
DEBVERSION=$(shell dpkg-parsechangelog -ldebian/changelog |grep Version|cut -d: -f3)
DLDIR=/mondo/htdocs/download.stoq.com.br/ubuntu

clean-docs:
	rm -fr doc/api
	rm -fr doc/howto

clean: clean-docs
	debclean
	rm -fr $(BUILDDIR)
	rm -f MANIFEST

docs:
	make -s -C doc api howto

web: clean-docs docs
	cp -r doc/api ${WEBDIR}
	cp -r doc/howto ${WEBDIR}
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
	cd $(BUILDDIR)/kiwi-$(VERSION) && debuild
	rm -fr $(BUILDDIR)/kiwi-$(VERSION)
	mv $(BUILDDIR)/* dist
	rm -fr $(BUILDDIR)

release: clean sdist bdist deb

release-tag:
	svn cp -m "Tag $(VERSION)" . svn+ssh://svn.async.com.br/pub/kiwi/tags/$(VERSION)

upload-release: release
	scp dist/$(TARBALL) gnome.org:
	ssh gnome.org install-module $(TARBALL)
	scp dist/kiwi-$(VERSION).win32.exe gnome.org:/ftp/pub/GNOME/binaries/win32/kiwi/

upload:
	cp dist/$(PACKAGE)*_$(DEBVERSION)*.deb $(DLDIR)
	for suffix in "gz" "dsc" "build" "changes"; do \
	  cp dist/$(PACKAGE)_$(DEBVERSION)*."$$suffix" $(DLDIR); \
	done
	cd $(DLDIR) && \
	cd $(DLDIR) && \
	  rm -f Release Release.gpg && \
	  dpkg-scanpackages . /dev/null > $(DLDIR)/Packages && \
	  dpkg-scansources . /dev/null > $(DLDIR)/Sources && \
	  apt-ftparchive release . > $(DLDIR)/Release && \
	  gpg -abs -o Release.gpg Release

.PHONY: docs web sdist bdist release deb upload upload-release
