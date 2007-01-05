def assert_raises(Exc, call, *arg, **kw):
    """Given an Exception, a callable, and its params, return an exception.
    """
    exc = None
    try:
        call(*arg, **kw)
    except Exception, exc:
        pass
    assert exc is not None, "no exception; expected %s" % Exc
    assert isinstance(exc, Exc), "raised %s, not %s" % (str(exc), str(Exc))
    return exc
