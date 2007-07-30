
class Scrimplate(object):
    """Represent a resource that can be called as wsgi.
    """


    def __call__(self, environ, start_response):
        """WSGI contract.
        """
    def get_response(self, request):
        """Extend WSGIHandler.get_response to bypass usual Django urlconf.
        """
        fspath = request.META['PATH_TRANSLATED']
        assert isfile(fspath), "This handler only serves files."
        request.urlconf = 'aspen.handlers.django_._' + self.filetype
        response = WSGIHandler.get_response(self, request)
        if 'Content-Type' not in response.headers:
            guess = mimetypes.guess_type(fspath, 'text/plain')[0]
            response.headers['Content-Type'] = guess
        return response

    def __build(self, fspath):
        """Given a filesystem path, return a compiled (but unbound) object.

        A scrimplate is a template with two optional Python components at the head
        of the file, delimited by an ASCII form feed (also called a page break, FF,
        ^L, \x0c, 12). The first Python section is exec'd when the scrimplate is
        first called, and the namespace it populates is saved for all subsequent
        runs (so make sure it is thread-safe!). The second Python section is exec'd
        within the template namespace each time the template is rendered.

        It is a requirement that subclasses do not mutate the import context at
        runtime.

        """
        scrimplate = open(fspath).read()

        numff = scrimplate.count(FORM_FEED)
        if numff == 0:
            script = imports = ""
            template = scrimplate
        elif numff == 1:
            imports = ""
            script, template = scrimplate.split(FORM_FEED)
        elif numff == 2:
            imports, script, template = scrimplate.split(FORM_FEED)
        else:
            raise SyntaxError( "Scrimplate <%s> may have at most two " % fspath
                             + "form feeds; it has %d." % numff
                              )

        # Standardize newlines.
        # =====================
        # compile requires \n, and doing it now makes the next line easier.

        imports = imports.replace('\r\n', '\n')
        script = script.replace('\r\n', '\n')


        # Pad the beginning of the script section so we get accurate tracebacks.
        # ======================================================================

        script = ''.join(['\n' for n in range(imports.count('\n')-2)]) + script


        # Prep our cachable objects and return.
        # =====================================

        c_imports = dict()
        exec compile(imports, fspath, 'exec') in c_imports
        c_script = compile(script, fspath, 'exec')
        c_template = Template(template)

        return (c_imports, c_script, c_template)


    def view(self, request):
        """Django view to exec and render the scrimplate at PATH_TRANSLATED.

        Your script section may raise SystemExit to terminate execution. Instantiate
        the SystemExit with an HttpResponse to bypass template rendering entirely;
        in all other cases, the template section will still be rendered.

        """
        imports, script, template = cache[request.META['PATH_TRANSLATED']]

        template_context = RequestContext(request, imports)

        if script:
            script_context = dict()
            for d in template_context.dicts:
                script_context.update(d)
            try:
                exec script in script_context
            except SystemExit, exc:
                if len(exc.args) >= 1:
                    response = exc.args[0]
                    if isinstance(response, HttpResponse):
                        return response
            template_context.update(script_context)

        response = HttpResponse(template.render(template_context))
        del response.headers['Content-Type'] # take this from the extension
        return response