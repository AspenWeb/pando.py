# Makefile to create documentation using the Python LaTeX system.

VERSION=0.3
MKHOWTO    = $(PYTHONSRC)/Doc/tools/mkhowto \
				--iconserver icons \
				--split 4 \
				--link 2 \
				--favicon icons/zeta.ico \
				--dir ./html \
				--logging \
				--up-link "http://www.zetadev.com/software/aspen/" \
				--up-title "aspen homepage" \
				--address "<a href=\"http://www.zetadev.com/software/aspen/\">aspen is Zeta software</a>. It is copyright &copy; 2006 by Chad Whitacre, and is offered free of charge, warranty, and restrictions." \
#				--style style.css


default: html

html: clean
	$(MKHOWTO) aspen.tex
	cp -r ../icons ./html/
	rm -rf ./html/icons/.svn
	rm -rf ../html && mv ./html ../

pdf:
	$(PYTHONSRC)/Doc/tools/mkhowto --pdf aspen.tex
	mv aspen.pdf ../aspen-$(VERSION).pdf

clean:
	rm -rf *~ *.aux *.idx *.ilg *.ind *.log *.toc *.bkm *.syn \
			*.pla *.eps *.pdf *.ps *.lof *.l2h *.tex2 *.dvi \
			../html ../*.pdf

all: html pdf clean
