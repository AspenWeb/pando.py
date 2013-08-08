
def pjaxify_content_type(request):
    """Put PJAX info into the content-type so simplates can switch on it.
       Only useful as an inbound_early hook so the dispatch will pay attention to it.
       To use, add this as an inbound_early hook, then make simplates that respond
       'as pjax-text/html' or whatever your fragment's content-type should be.
    """
    
    if request.headers.get('X-PJAX'):
        ct = request.headers.get('Content-type', '')
        request.headers['Content-type'] = 'pjax-' + ct

