def assert_raises(Exc, call, *arg, **kw):
    exc = None
    try:
        call(*arg, **kw)
    except Exception, exc:
        pass
    assert exc is not None, "no exception; expected %s" % Exc
    assert isinstance(exc, Exc), "raised %s, not %s" % (str(exc), str(Exc))
    return exc
