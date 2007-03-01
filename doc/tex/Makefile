# Makefile to create documentation using the Python LaTeX system.

VERSION=0.7.1
MKHOWTO    = $(PYTHONSRC)/Doc/tools/mkhowto \
				--iconserver icons \
				--split 4 \
				--link 2 \
				--favicon icons/zeta.ico \
				--dir ./html \
				--logging \
				--up-link "http://www.zetadev.com/software/aspen/" \
				--up-title "aspen homepage" \
				--address "<a href=\"http://www.zetadev.com/software/aspen/\">Aspen</a> is copyright &copy; 2006-2007 by Chad Whitacre and contributors, and is offered under the MIT license." \
#				--style style.css


default: html

html:
	$(MKHOWTO) aspen.tex
	cp -r ../icons ./html/
	rm -rf ./html/icons/.svn
	mv -f ./html/* ../html/
	rm -rf ./html

pdf:
	$(PYTHONSRC)/Doc/tools/mkhowto --pdf aspen.tex
	mv aspen.pdf ../aspen-$(VERSION).pdf

clean:
	rm -rf *~ *.aux *.idx *.ilg *.ind *.log *.toc *.bkm *.syn \
			*.pla *.eps *.pdf *.ps *.lof *.l2h *.tex2 *.dvi \
			../html/WARNINGS ../html/*.* ../html/icons ../*.pdf \
			./html/

all: html pdf clean
