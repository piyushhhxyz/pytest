import pytest
from _pytest._code.code import ExceptionInfo
from _pytest.pathlib import Path
from _pytest.reports import CollectReport
from _pytest.reports import TestReport


class TestReportSerialization:
    def test_xdist_longrepr_to_str_issue_241(self, testdir):
        """
        Regarding issue pytest-xdist#241

        This test came originally from test_remote.py in xdist (ca03269).
        """
        testdir.makepyfile(
            """
            def test_a(): assert False
            def test_b(): pass
        """
        )
        reprec = testdir.inline_run()
        reports = reprec.getreports("pytest_runtest_logreport")
        assert len(reports) == 6
        test_a_call = reports[1]
        assert test_a_call.when == "call"
        assert test_a_call.outcome == "failed"
        assert test_a_call._to_json()["longrepr"]["reprtraceback"]["style"] == "long"
        test_b_call = reports[4]
        assert test_b_call.when == "call"
        assert test_b_call.outcome == "passed"
        assert test_b_call._to_json()["longrepr"] is None

    def test_xdist_report_longrepr_reprcrash_130(self, testdir):
        """Regarding issue pytest-xdist#130

        This test came originally from test_remote.py in xdist (ca03269).
        """
        reprec = testdir.inline_runsource(
            """
                    def test_fail():
                        assert False, 'Expected Message'
                """
        )
        reports = reprec.getreports("pytest_runtest_logreport")
        assert len(reports) == 3
        rep = reports[1]
        added_section = ("Failure Metadata", "metadata metadata", "*")
        rep.longrepr.sections.append(added_section)
        d = rep._to_json()
        a = TestReport._from_json(d)
        # Check assembled == rep
        assert a.__dict__.keys() == rep.__dict__.keys()
        for key in rep.__dict__.keys():
            if key != "longrepr":
                assert getattr(a, key) == getattr(rep, key)
        assert rep.longrepr.reprcrash.lineno == a.longrepr.reprcrash.lineno
        assert rep.longrepr.reprcrash.message == a.longrepr.reprcrash.message
        assert rep.longrepr.reprcrash.path == a.longrepr.reprcrash.path
        assert rep.longrepr.reprtraceback.entrysep == a.longrepr.reprtraceback.entrysep
        assert (
            rep.longrepr.reprtraceback.extraline == a.longrepr.reprtraceback.extraline
        )
        assert rep.longrepr.reprtraceback.style == a.longrepr.reprtraceback.style
        assert rep.longrepr.sections == a.longrepr.sections
        # Missing section attribute PR171
        assert added_section in a.longrepr.sections

    def test_reprentries_serialization_170(self, testdir):
        """Regarding issue pytest-xdist#170

        This test came originally from test_remote.py in xdist (ca03269).
        """
        from _pytest._code.code import ReprEntry

        reprec = testdir.inline_runsource(
            """
                            def test_repr_entry():
                                x = 0
                                assert x
                        """,
            "--showlocals",
        )
        reports = reprec.getreports("pytest_runtest_logreport")
        assert len(reports) == 3
        rep = reports[1]
        d = rep._to_json()
        a = TestReport._from_json(d)

        rep_entries = rep.longrepr.reprtraceback.reprentries
        a_entries = a.longrepr.reprtraceback.reprentries
        for i in range(len(a_entries)):
            assert isinstance(rep_entries[i], ReprEntry)
            assert rep_entries[i].lines == a_entries[i].lines
            assert rep_entries[i].reprfileloc.lineno == a_entries[i].reprfileloc.lineno
            assert (
                rep_entries[i].reprfileloc.message == a_entries[i].reprfileloc.message
            )
            assert rep_entries[i].reprfileloc.path == a_entries[i].reprfileloc.path
            assert rep_entries[i].reprfuncargs.args == a_entries[i].reprfuncargs.args
            assert rep_entries[i].reprlocals.lines == a_entries[i].reprlocals.lines
            assert rep_entries[i].style == a_entries[i].style

    def test_reprentries_serialization_196(self, testdir):
        """Regarding issue pytest-xdist#196

        This test came originally from test_remote.py in xdist (ca03269).
        """
        from _pytest._code.code import ReprEntryNative

        reprec = testdir.inline_runsource(
            """
                            def test_repr_entry_native():
                                x = 0
                                assert x
                        """,
            "--tb=native",
        )
        reports = reprec.getreports("pytest_runtest_logreport")
        assert len(reports) == 3
        rep = reports[1]
        d = rep._to_json()
        a = TestReport._from_json(d)

        rep_entries = rep.longrepr.reprtraceback.reprentries
        a_entries = a.longrepr.reprtraceback.reprentries
        for i in range(len(a_entries)):
            assert isinstance(rep_entries[i], ReprEntryNative)
            assert rep_entries[i].lines == a_entries[i].lines

    def test_itemreport_outcomes(self, testdir):
        """
        This test came originally from test_remote.py in xdist (ca03269).
        """
        reprec = testdir.inline_runsource(
            """
            import py
            def test_pass(): pass
            def test_fail(): 0/0
            @py.test.mark.skipif("True")
            def test_skip(): pass
            def test_skip_imperative():
                py.test.skip("hello")
            @py.test.mark.xfail("True")
            def test_xfail(): 0/0
            def test_xfail_imperative():
                py.test.xfail("hello")
        """
        )
        reports = reprec.getreports("pytest_runtest_logreport")
        assert len(reports) == 17  # with setup/teardown "passed" reports
        for rep in reports:
            d = rep._to_json()
            newrep = TestReport._from_json(d)
            assert newrep.passed == rep.passed
            assert newrep.failed == rep.failed
            assert newrep.skipped == rep.skipped
            if newrep.skipped and not hasattr(newrep, "wasxfail"):
                assert len(newrep.longrepr) == 3
            assert newrep.outcome == rep.outcome
            assert newrep.when == rep.when
            assert newrep.keywords == rep.keywords
            if rep.failed:
                assert newrep.longreprtext == rep.longreprtext

    def test_collectreport_passed(self, testdir):
        """This test came originally from test_remote.py in xdist (ca03269)."""
        reprec = testdir.inline_runsource("def test_func(): pass")
        reports = reprec.getreports("pytest_collectreport")
        for rep in reports:
            d = rep._to_json()
            newrep = CollectReport._from_json(d)
            assert newrep.passed == rep.passed
            assert newrep.failed == rep.failed
            assert newrep.skipped == rep.skipped

    def test_collectreport_fail(self, testdir):
        """This test came originally from test_remote.py in xdist (ca03269)."""
        reprec = testdir.inline_runsource("qwe abc")
        reports = reprec.getreports("pytest_collectreport")
        assert reports
        for rep in reports:
            d = rep._to_json()
            newrep = CollectReport._from_json(d)
            assert newrep.passed == rep.passed
            assert newrep.failed == rep.failed
            assert newrep.skipped == rep.skipped
            if rep.failed:
                assert newrep.longrepr == str(rep.longrepr)

    def test_extended_report_deserialization(self, testdir):
        """This test came originally from test_remote.py in xdist (ca03269)."""
        reprec = testdir.inline_runsource("qwe abc")
        reports = reprec.getreports("pytest_collectreport")
        assert reports
        for rep in reports:
            rep.extra = True
            d = rep._to_json()
            newrep = CollectReport._from_json(d)
            assert newrep.extra
            assert newrep.passed == rep.passed
            assert newrep.failed == rep.failed
            assert newrep.skipped == rep.skipped
            if rep.failed:
                assert newrep.longrepr == str(rep.longrepr)

    def test_paths_support(self, testdir):
        """Report attributes which are py.path or pathlib objects should become strings."""
        testdir.makepyfile(
            """
            def test_a():
                assert False
        """
        )
        reprec = testdir.inline_run()
        reports = reprec.getreports("pytest_runtest_logreport")
        assert len(reports) == 3
        test_a_call = reports[1]
        test_a_call.path1 = testdir.tmpdir
        test_a_call.path2 = Path(testdir.tmpdir)
        data = test_a_call._to_json()
        assert data["path1"] == str(testdir.tmpdir)
        assert data["path2"] == str(testdir.tmpdir)

    def test_unserialization_failure(self, testdir):
        """Check handling of failure during unserialization of report types."""
        testdir.makepyfile(
            """
            def test_a():
                assert False
        """
        )
        reprec = testdir.inline_run()
        reports = reprec.getreports("pytest_runtest_logreport")
        assert len(reports) == 3
        test_a_call = reports[1]
        data = test_a_call._to_json()
        entry = data["longrepr"]["reprtraceback"]["reprentries"][0]
        assert entry["type"] == "ReprEntry"

        entry["type"] = "Unknown"
        with pytest.raises(
            RuntimeError, match="INTERNALERROR: Unknown entry type returned: Unknown"
        ):
            TestReport._from_json(data)


class TestHooks:
    """Test that the hooks are working correctly for plugins"""

    def test_test_report(self, testdir, pytestconfig):
        testdir.makepyfile(
            """
            def test_a(): assert False
            def test_b(): pass
        """
        )
        reprec = testdir.inline_run()
        reports = reprec.getreports("pytest_runtest_logreport")
        assert len(reports) == 6
        for rep in reports:
            data = pytestconfig.hook.pytest_report_to_serializable(
                config=pytestconfig, report=rep
            )
            assert data["_report_type"] == "TestReport"
            new_rep = pytestconfig.hook.pytest_report_from_serializable(
                config=pytestconfig, data=data
            )
            assert new_rep.nodeid == rep.nodeid
            assert new_rep.when == rep.when
            assert new_rep.outcome == rep.outcome

    def test_collect_report(self, testdir, pytestconfig):
        testdir.makepyfile(
            """
            def test_a(): assert False
            def test_b(): pass
        """
        )
        reprec = testdir.inline_run()
        reports = reprec.getreports("pytest_collectreport")
        assert len(reports) == 2
        for rep in reports:
            data = pytestconfig.hook.pytest_report_to_serializable(
                config=pytestconfig, report=rep
            )
            assert data["_report_type"] == "CollectReport"
            new_rep = pytestconfig.hook.pytest_report_from_serializable(
                config=pytestconfig, data=data
            )
            assert new_rep.nodeid == rep.nodeid
            assert new_rep.when == "collect"
            assert new_rep.outcome == rep.outcome

    @pytest.mark.parametrize(
        "hook_name", ["pytest_runtest_logreport", "pytest_collectreport"]
    )
    def test_invalid_report_types(self, testdir, pytestconfig, hook_name):
        testdir.makepyfile(
            """
            def test_a(): pass
            """
        )
        reprec = testdir.inline_run()
        reports = reprec.getreports(hook_name)
        assert reports
        rep = reports[0]
        data = pytestconfig.hook.pytest_report_to_serializable(
            config=pytestconfig, report=rep
        )
        data["_report_type"] = "Unknown"
        with pytest.raises(AssertionError):
            _ = pytestconfig.hook.pytest_report_from_serializable(
                config=pytestconfig, data=data
            )


class TestChainedExceptionSerializationRepr:
    """Regression tests for chained exception serialization (xdist issue).

    When xdist serializes a TestReport via _to_json()/_from_json(), chained
    exceptions must survive the round-trip so the full chain is displayed,
    not just the final (leaf) exception.
    """

    def _make_report(self, longrepr):
        return TestReport(
            nodeid="test_chained",
            location=("test_chained.py", 1, "test_chained"),
            keywords={},
            outcome="failed",
            longrepr=longrepr,
            when="call",
        )

    def _roundtrip(self, longrepr):
        report = self._make_report(longrepr)
        data = report._to_json()
        restored = TestReport._from_json(data)
        return restored.longreprtext

    def test_chained_exception_with_from_roundtrip(self):
        """Explicit chaining via 'raise X from Y' must survive serialization."""
        try:
            try:
                try:
                    raise ValueError(11)
                except Exception as e1:
                    raise ValueError(12) from e1
            except Exception as e2:
                raise ValueError(13) from e2
        except Exception:
            ei = ExceptionInfo.from_current()

        result = self._roundtrip(ei.getrepr(chain=True))

        assert "ValueError: 11" in result
        assert "ValueError: 12" in result
        assert "ValueError: 13" in result
        assert "The above exception was the direct cause of the following exception:" in result

    def test_chained_exception_without_from_roundtrip(self):
        """Implicit chaining via __context__ must survive serialization."""
        try:
            try:
                try:
                    raise ValueError(21)
                except Exception:
                    raise ValueError(22)
            except Exception:
                raise ValueError(23)
        except Exception:
            ei = ExceptionInfo.from_current()

        result = self._roundtrip(ei.getrepr(chain=True))

        assert "ValueError: 21" in result
        assert "ValueError: 22" in result
        assert "ValueError: 23" in result
        assert "During handling of the above exception, another exception occurred:" in result

    def test_chain_false_still_works(self):
        """chain=False (single exception) must still round-trip correctly."""
        try:
            raise ValueError(99)
        except Exception:
            ei = ExceptionInfo.from_current()

        result = self._roundtrip(ei.getrepr(chain=False))
        assert "ValueError: 99" in result

    def test_backward_compat_no_chain_key(self):
        """Old payloads without a 'chain' key must still deserialize (backward compat)."""
        try:
            raise ValueError(42)
        except Exception:
            ei = ExceptionInfo.from_current()

        report = self._make_report(ei.getrepr(chain=True))
        data = report._to_json()
        # Simulate an older sender that didn't include the chain key
        del data["longrepr"]["chain"]
        restored = TestReport._from_json(data)
        assert "ValueError: 42" in restored.longreprtext

    def test_chained_exception_reprcrash_points_to_outermost(self):
        """reprcrash must point to the outermost (final raised) exception."""
        try:
            try:
                raise ValueError(11)
            except Exception as e1:
                raise ValueError(12) from e1
        except Exception:
            ei = ExceptionInfo.from_current()

        report = self._make_report(ei.getrepr(chain=True))
        data = report._to_json()
        restored = TestReport._from_json(data)
        # reprcrash should reference the outermost exception (ValueError: 12)
        assert restored.longrepr.reprcrash is not None
        assert "ValueError: 12" in restored.longrepr.reprcrash.message

    def test_chained_exception_collect_report_roundtrip(self):
        """CollectReport with a chained exception must also round-trip correctly."""
        try:
            try:
                raise ValueError(51)
            except Exception as e1:
                raise ValueError(52) from e1
        except Exception:
            ei = ExceptionInfo.from_current()

        longrepr = ei.getrepr(chain=True)
        report = CollectReport(
            nodeid="test_chained.py",
            outcome="failed",
            longrepr=longrepr,
            result=[],
        )
        data = report._to_json()
        restored = CollectReport._from_json(data)
        result = restored.longreprtext
        assert "ValueError: 51" in result
        assert "ValueError: 52" in result
        assert "The above exception was the direct cause of the following exception:" in result
