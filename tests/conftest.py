def pytest_sessionfinish( session, exitstatus ):
    if exitstatus == 5:  # pytest exit code for "no tests collected"
        session.exitstatus = 0
