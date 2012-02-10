# Tweak these to your local configuration. Note that mkhowto requires
# LaTeX and latex2html.

MKHOWTO=/mondo/src/PYTHON/2.4.1/Doc/tools/mkhowto

# No user-serviceable parts below this line

STYLE="PRE { border-left: 1px dashed blue;		\
		  border-right: 1px dashed blue;		\
		  border-top: 1px dashed blue;			\
		  border-bottom: 1px dashed blue;		\
		  padding: 1em; margin-right: 2.5em;	\
		  margin-left: 2.5em; }"
NAME=Kiwi
URL=http://www.async.com.br/projects/kiwi/
FIXIMG=perl -p -i -e 's/WIDTH=\"[0-9]+\" HEIGHT=\"[0-9]+\"//'

all: api howto

howto: howto.tex
	@echo Creating howto
	@mkdir -p howto
	@$(MKHOWTO) -k --image-type png --a4 
	@echo $(STYLE) >> howto/howto.css
	@latex howto
	@latex howto
	@dvips howto
	@$(FIXIMG) howto/*.html
	@echo Copying examples and images
	@cp images/diary.png     howto/img1.png
	@cp images/simple.png    howto/img2.png
	@cp images/london.png    howto/img3.png
	@cp images/london2.png   howto/img4.png
	@cp images/shell1.png    howto/img5.png
	@cp images/shell2.png    howto/img6.png
	@cp images/faren.png     howto/img7.png
	@cp images/simple2.png   howto/img8.png
	@cp images/simple3.png   howto/img9.png
	@cp images/news2.png     howto/img10.png
	@cp images/news3.png     howto/img11.png
# 	@cp images/newsform.png  howto/img12.png
# 	@cp images/newsform2.png howto/img13.png
# 	@cp images/newsform4.png howto/img14.png
	@cp ../examples/framework/person/Person.glade howto/
	@cp ../examples/framework/faren/faren.glade howto/

api:
	@echo Creating API documentation

clean:
	rm -rf api/ howto/ *.log *.aux *.l2h *.dvi *.ps *.bak *~

.PHONY: clean
