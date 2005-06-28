# Tweak these to your local configuration. 

EPYDOC=epydoc

# No user-serviceable parts below this line

MODULES = \
	../kiwi/__init__.py 		\
	../kiwi/accessors.py 		\
	../kiwi/utils.py 			\
	../kiwi/Controllers.py 	\
	../kiwi/Delegates.py 		\
	../kiwi/Proxies.py 		\
	../kiwi/Models.py 			\
	../kiwi/Views.py 			\
	../kiwi/Widgets/

STYLE="PRE { border-left: 1px dashed blue;		\
		  border-right: 1px dashed blue;		\
		  border-top: 1px dashed blue;			\
		  border-bottom: 1px dashed blue;		\
		  padding: 1em; margin-right: 2.5em;	\
		  margin-left: 2.5em; }"
NAME=kiwi
URL=http://www.async.com.br/projects/kiwi/

all: api

api: $(MODULES)
	mkdir -p api
	$(EPYDOC) -c white --no-frames -o api -u $(URL) -n $(NAME) $(MODULES) 
	touch api

apicheck: 
	epydoc --check $(MODULES) 

clean:
	rm -rf api/ howto/ *.log *.aux *.l2h *.dvi *.ps *.bak *~

.PHONY: apicheck clean
