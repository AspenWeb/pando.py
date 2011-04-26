from aspen import cli
from aspen.tests.fsfix import attach_teardown


def est_starts_on_8080():
    cli.main([])
    assert 0


attach_teardown(globals())
