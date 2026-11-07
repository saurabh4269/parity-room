#!/usr/bin/env python3
"""Offline tests for the observer. Feeds raw API responses captured from the LIVE system
(observer/testdata/, see capture_testdata.py) through server.compose() and validates the result with the
dashboard's own contract validator (dashboard/check-fixtures.py). Run:  python3 observer/test_state.py"""
import copy
import importlib.util
import json
import os
os.environ["PARITY_ROOM"] = "parity-room"   # tests must never depend on the live room (work/room.txt)
import sys
import threading
import unittest
import urllib.error
import urllib.request

sys.dont_write_bytecode = True   # never leave __pycache__ in dashboard/ (we import its validator)
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import server  # noqa: E402

DASH = os.path.join(os.path.dirname(HERE), "dashboard")
_spec = importlib.util.spec_from_file_location("check_fixtures", os.path.join(DASH, "check-fixtures.py"))
contract = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(contract)


def load(name):
    with open(os.path.join(HERE, "testdata", name), encoding="utf-8") as fh:
        return json.load(fh)


RAW_FILES = {"rooms": "gateway_rooms", "room": "gateway_room", "roles": "gateway_roles", "agents": "gateway_agents",
             "controllers": "gateway_controllers", "mm_channel": "mm_channel", "mm_posts": "mm_posts",
             "mm_members": "mm_members", "mm_users": "mm_users"}


def live_raw():
    raw = {k: load(v + ".json") for k, v in RAW_FILES.items()}
    raw["documents"] = {n: load("gateway_doc_%s.json" % n) for n in ("matrix-mac", "matrix-linux")}
    return raw


def fixture(name):
    with open(os.path.join(DASH, "fixtures", "state-%s.json" % name), encoding="utf-8") as fh:
        return json.load(fh)


def cell_ok(at="2026-11-07T14:00:00Z"):
    return {"status": "pass", "at": at, "detail": None}


def set_matrix(raw, env, sha=None, ran_at=None, results=None, content=None):
    """Edit the captured matrix-<env> document the way an agent would write a new run."""
    doc = raw["documents"]["matrix-" + env]
    if content is not None:
        doc["content"] = content
        return
    data = json.loads(doc["content"])
    if sha is not None:
        data["change"]["head_sha"] = sha
    if ran_at is not None:
        data["ran_at"] = ran_at
    for cid, res in (results or {}).items():
        data["results"][cid] = res
    doc["content"] = json.dumps(data, indent=2)


def green_same_sha(sha="3a346cb"):
    raw = live_raw()
    set_matrix(raw, "mac", sha=sha, ran_at="2026-11-07T13:53:00Z")
    set_matrix(raw, "linux", sha=sha, ran_at="2026-11-07T13:52:00Z")
    return raw


class ContractMixin:
    def assert_valid(self, state):
        rep = contract.validate(state)
        self.assertEqual(rep.errors, [], rep.errors)
        return rep

    def statuses(self, state, env):
        return {c: r["status"] for c, r in state["results"][env].items()}


class TestContractShape(ContractMixin, unittest.TestCase):
    def test_validator_accepts_the_dashboard_fixtures(self):
        for n in ("pending", "failing", "running", "verified"):
            self.assert_valid(fixture(n))

    def test_live_capture_is_valid_and_has_exact_fixture_shape(self):
        state = server.compose(live_raw())
        self.assert_valid(state)
        fx = fixture("verified")
        self.assertEqual(set(state) - {"links"}, set(fx))  # links is the contract's optional key
        self.assertEqual(state["schema"], 1)
        self.assertEqual(state["checks"], fx["checks"])
        self.assertEqual([e["id"] for e in state["environments"]], ["mac", "linux"])
        for e, fe in zip(state["environments"], fx["environments"]):
            self.assertEqual(set(e), set(fe))
            self.assertEqual(set(e["facts"]), set(fe["facts"]))
        cell = state["results"]["mac"]["settings"]
        self.assertEqual(set(cell), {"status", "at", "detail"})
        self.assertEqual(set(state["room"]), set(fx["room"]))
        for a in state["room"]["agents"]:
            self.assertEqual(set(a), set(fx["room"]["agents"][0]))
        for h in state["room"]["humans"]:
            self.assertEqual(set(h), {"name", "title"})
        for ev in state["timeline"]:
            self.assertEqual(set(ev), set(fx["timeline"][0]))
        self.assertEqual(state["change"]["title"], "feat: weekly digest report")
        self.assertEqual(state["change"]["author"], "Priya")
        self.assertEqual(state["links"], {"room": "http://localhost:8065/switch/channels/parity-room"})
        json.dumps(state)  # serialisable

    def test_empty_raw_is_a_valid_pending_state(self):
        for raw in ({}, None, {"rooms": []}, {"rooms": "garbage", "room": 5, "documents": []}):
            state = server.compose(raw)
            self.assert_valid(state)
            self.assertEqual(state["status"], "pending")


class TestDerivation(ContractMixin, unittest.TestCase):
    def test_live_capture_mac_is_stale_so_overall_running(self):
        # As captured: matrix-mac is for b41bd7a (before the fix), matrix-linux for 3a346cb.
        state = server.compose(live_raw())
        self.assertEqual(state["change"]["head_sha"], "3a346cb")
        self.assertEqual(set(self.statuses(state, "mac").values()), {"running"})
        self.assertEqual(set(self.statuses(state, "linux").values()), {"pass"})
        self.assertEqual(state["status"], "running")
        for c in state["results"]["mac"].values():
            self.assertEqual((c["at"], c["detail"]), (None, None))
        # facts still come from the (stale) mac document
        self.assertEqual(state["environments"][0]["facts"]["tz"], "Asia/Kolkata")

    def test_a_both_green_same_sha_is_verified(self):
        state = server.compose(green_same_sha())
        rep = self.assert_valid(state)
        self.assertEqual(rep.warnings, [])
        self.assertEqual(state["status"], "verified")
        for env in ("mac", "linux"):
            self.assertEqual(set(self.statuses(state, env).values()), {"pass"})
        self.assertEqual(state["change"]["branch"], "feat/weekly-report")
        self.assertEqual(state["change"]["head_sha"], "3a346cb")
        self.assertEqual(state["results"]["mac"]["stamp"]["at"], "2026-11-07T13:51:18Z")
        self.assertEqual(state["environments"][1]["facts"],
                         {"os": "Ubuntu 22.04.5 LTS aarch64", "python": "3.10.12", "tz": "UTC", "fs": "case-sensitive"})

    def test_b_linux_red_is_failing(self):
        raw = green_same_sha()
        set_matrix(raw, "linux", results={
            "settings": {"status": "fail", "at": "2026-11-07T13:52:00Z", "detail": "FileNotFoundError: config/Settings.json"},
            "stamp": {"status": "fail", "at": "2026-11-07T13:52:00Z", "detail": "AttributeError: datetime.UTC"}})
        state = server.compose(raw)
        rep = self.assert_valid(state)
        self.assertEqual(rep.warnings, [])
        self.assertEqual(state["status"], "failing")
        self.assertEqual(self.statuses(state, "linux"), {"settings": "fail", "stamp": "fail", "buckets": "pass"})
        self.assertEqual(state["results"]["linux"]["settings"]["detail"], "FileNotFoundError: config/Settings.json")
        self.assertEqual(set(self.statuses(state, "mac").values()), {"pass"})

    def test_c_stale_linux_is_running(self):
        raw = live_raw()
        # mac re-ran later on a newer commit; linux still holds a red result for the old commit
        set_matrix(raw, "mac", sha="deadbee", ran_at="2026-11-07T14:10:00Z")
        set_matrix(raw, "linux", sha="b41bd7a", ran_at="2026-11-07T13:51:52Z",
                   results={"settings": {"status": "fail", "at": "2026-11-07T13:51:52Z", "detail": "old failure"}})
        state = server.compose(raw)
        self.assert_valid(state)
        self.assertEqual(state["change"]["head_sha"], "deadbee")
        self.assertEqual(self.statuses(state, "linux"), {"settings": "running", "stamp": "running", "buckets": "running"})
        self.assertEqual(state["results"]["linux"]["settings"], {"status": "running", "at": None, "detail": None})
        self.assertEqual(set(self.statuses(state, "mac").values()), {"pass"})
        self.assertEqual(state["status"], "running")   # a stale failure must not read as failing

    def test_current_failure_beats_stale_running(self):
        raw = live_raw()
        set_matrix(raw, "mac", sha="deadbee", ran_at="2026-11-07T14:10:00Z",
                   results={"buckets": {"status": "fail", "at": "2026-11-07T14:10:00Z", "detail": "boom"}})
        state = server.compose(raw)
        self.assert_valid(state)
        self.assertEqual(self.statuses(state, "linux"), {"settings": "running", "stamp": "running", "buckets": "running"})
        self.assertEqual(state["status"], "failing")

    def test_d_invalid_json_doc_is_pending_with_detail(self):
        for bad in ("this is {not json", "{\"schema\": 1,", "[1, 2]"):
            raw = green_same_sha()
            set_matrix(raw, "mac", content=bad)
            state = server.compose(raw)
            self.assert_valid(state)
            self.assertEqual(set(self.statuses(state, "mac").values()), {"pending"}, bad)
            want = "matrix document is not valid JSON" if bad != "[1, 2]" else "matrix document is not a schema-1 evidence object"
            for c in state["results"]["mac"].values():
                self.assertEqual(c["detail"], want)
                self.assertIsNone(c["at"])
            self.assertEqual(state["environments"][0]["facts"], {k: "unknown" for k in server.FACT_KEYS})
            self.assertEqual(state["status"], "pending")            # nothing is verified without the mac evidence
            self.assertEqual(state["change"]["head_sha"], "3a346cb")  # still from the valid linux doc

    def test_invalid_doc_does_not_hide_a_real_failure(self):
        raw = green_same_sha()
        set_matrix(raw, "mac", content="garbage")
        set_matrix(raw, "linux", results={"buckets": {"status": "fail", "at": "2026-11-07T13:52:00Z", "detail": "x"}})
        self.assertEqual(server.compose(raw)["status"], "failing")

    def test_missing_or_empty_doc_is_pending_without_detail(self):
        for mutate in (lambda r: r["documents"].update({"matrix-mac": None}),
                       lambda r: r["documents"].pop("matrix-mac"),
                       lambda r: r["documents"]["matrix-mac"].update({"content": ""})):
            raw = green_same_sha()
            mutate(raw)
            state = server.compose(raw)
            self.assert_valid(state)
            self.assertEqual(state["results"]["mac"]["settings"], {"status": "pending", "at": None, "detail": None})
            self.assertEqual(state["environments"][0]["facts"], {k: "unknown" for k in server.FACT_KEYS})
            self.assertEqual(state["status"], "pending")

    def test_no_docs_at_all_is_pending_with_blank_change(self):
        raw = live_raw()
        raw["documents"] = {"matrix-mac": None, "matrix-linux": None}
        state = server.compose(raw)
        self.assert_valid(state)
        self.assertEqual(state["status"], "pending")
        self.assertEqual((state["change"]["branch"], state["change"]["head_sha"]), ("", ""))
        # the room itself is real and still reported
        self.assertEqual([a["name"] for a in state["room"]["agents"]], ["dev-mac", "qa-linux"])

    def test_malformed_results_become_pending_with_a_reason(self):
        raw = green_same_sha()
        set_matrix(raw, "linux", results={"settings": {"status": "PASSED", "at": "nope", "detail": None}})
        data = json.loads(raw["documents"]["matrix-linux"]["content"])
        del data["results"]["stamp"]
        raw["documents"]["matrix-linux"]["content"] = json.dumps(data)
        state = server.compose(raw)
        self.assert_valid(state)
        self.assertEqual(state["results"]["linux"]["settings"]["status"], "pending")
        self.assertIn("unrecognised status", state["results"]["linux"]["settings"]["detail"])
        self.assertEqual(state["results"]["linux"]["stamp"]["detail"], "check missing from matrix document")
        self.assertEqual(state["status"], "pending")

    def test_wrong_env_in_document_is_rejected(self):
        raw = green_same_sha()
        data = json.loads(raw["documents"]["matrix-mac"]["content"])
        data["env"] = "linux"
        raw["documents"]["matrix-mac"]["content"] = json.dumps(data)
        state = server.compose(raw)
        self.assertIn("expected 'mac'", state["results"]["mac"]["settings"]["detail"])
        self.assertEqual(state["status"], "pending")

    def test_e_missing_room_is_pending(self):
        raw = live_raw()
        raw["rooms"] = [r for r in raw["rooms"] if r["name"] != "parity-room"]
        state = server.compose(raw)
        self.assert_valid(state)
        self.assertEqual(state["status"], "pending")
        self.assertEqual(state["timeline"], [])
        self.assertEqual(state["room"], {"name": "parity-room", "agents": [], "humans": []})
        for env in ("mac", "linux"):
            self.assertEqual(set(self.statuses(state, env).values()), {"pending"})
        self.assertEqual([e["facts"]["os"] for e in state["environments"]], ["unknown", "unknown"])
        self.assertEqual(state["change"]["head_sha"], "")

    def test_archived_room_counts_as_missing(self):
        raw = live_raw()
        for r in raw["rooms"]:
            r["archived"] = True
        self.assertEqual(server.compose(raw)["status"], "pending")

    def test_equal_sha_but_newer_ran_at_picks_change_from_newest(self):
        raw = green_same_sha()
        set_matrix(raw, "linux", sha="3a346cb", ran_at="2026-11-07T13:59:00Z")
        self.assertEqual(server.compose(raw)["status"], "verified")


class TestRoom(ContractMixin, unittest.TestCase):
    def test_agents_roles_online_and_machines(self):
        state = server.compose(live_raw())
        agents = {a["name"]: a for a in state["room"]["agents"]}
        self.assertEqual(set(agents), {"dev-mac", "qa-linux"})
        self.assertEqual(agents["dev-mac"], {"name": "dev-mac", "provider": "Claude Code", "machine": "mac-host",
                                             "online": True, "roles": [{"name": "implementer", "mode": "exclusive"}]})
        self.assertEqual(agents["qa-linux"], {"name": "qa-linux", "provider": "Codex", "machine": "linux-box",
                                              "online": True, "roles": [{"name": "verifier", "mode": "shared"}]})
        self.assertEqual([e["agent"] for e in state["environments"]], ["dev-mac", "qa-linux"])

    def test_offline_when_not_live(self):
        raw = live_raw()
        for k in raw["room"]["agent_statuses"]:
            raw["room"]["agent_statuses"][k] = "offline"
        self.assertEqual([a["online"] for a in server.compose(raw)["room"]["agents"]], [False, False])

    def test_machine_comes_from_controllers_and_falls_back_to_defaults(self):
        raw = live_raw()
        for c in raw["controllers"]:
            c["name"] = "renamed-" + c["name"]
        state = server.compose(raw)
        self.assertEqual([a["machine"] for a in state["room"]["agents"]], ["renamed-mac-host", "renamed-linux-box"])
        raw["controllers"] = None
        state = server.compose(raw)
        self.assertEqual([e["machine"] for e in state["environments"]], ["mac-host", "linux-box"])
        self.assert_valid(state)

    def test_humans_come_from_mattermost_with_titles(self):
        humans = {h["name"]: h["title"] for h in server.compose(live_raw())["room"]["humans"]}
        self.assertEqual(humans["maya"], "PM")
        self.assertEqual(humans["sam"], "QA lead")
        for noise in ("admin", "switch-admin", "user", "dev-mac", "qa-linux"):
            self.assertNotIn(noise, humans)
        names = [h["name"] for h in server.compose(live_raw())["room"]["humans"]]
        self.assertEqual(names[:2], ["maya", "sam"])

    def test_humans_fall_back_to_static_titles_without_mattermost(self):
        raw = live_raw()
        raw.pop("mm_users")
        raw.pop("mm_members")
        raw.pop("mm_posts")
        state = server.compose(raw)
        self.assertEqual(state["room"]["humans"], [{"name": "maya", "title": "PM"}, {"name": "sam", "title": "QA lead"}])
        self.assertEqual(state["timeline"], [])
        self.assert_valid(state)


class TestTimeline(unittest.TestCase):
    def setUp(self):
        self.state = server.compose(live_raw())
        self.tl = self.state["timeline"]

    def test_shape_order_and_bounds(self):
        self.assertTrue(0 < len(self.tl) <= server.TIMELINE_MAX)
        self.assertEqual([e["at"] for e in self.tl], sorted(e["at"] for e in self.tl))
        for e in self.tl:
            self.assertIn(e["kind"], ("human", "agent"))
            self.assertLessEqual(len(e["title"]), server.TITLE_MAX)
            self.assertLessEqual(len(e["detail"]), server.DETAIL_MAX)
            self.assertTrue(e["title"])
            self.assertRegex(e["at"], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")

    def test_kind_matches_is_bot_and_actors_are_real_usernames(self):
        users = {u["username"]: u for u in load("mm_users.json").values()}
        for e in self.tl:
            self.assertEqual(e["kind"], "agent" if users[e["actor"]]["is_bot"] else "human")
        self.assertTrue({"maya", "sam"} <= {e["actor"] for e in self.tl} or len(self.tl) == server.TIMELINE_MAX)

    def test_noise_is_filtered(self):
        for e in self.tl:
            self.assertNotIn(e["actor"], ("admin", "switch-admin"))
            blob = e["title"] + " " + e["detail"]
            for bad in ("Worked for", "tool calls", "room document", "Starting a session", "assumed the",
                        "joined the channel", "added to the channel", "**", "```"):
                self.assertNotIn(bad, blob)

    def test_all_meaningful_posts_when_few(self):
        raw = live_raw()
        # keep only the first 16 root conversation posts (before the late extras) to see the whole story
        posts = raw["mm_posts"]
        keep = sorted(posts["order"], key=lambda i: posts["posts"][i]["create_at"])
        cutoff = next(posts["posts"][i]["create_at"] for i in keep
                      if posts["posts"][i]["message"].startswith("Merged feat/weekly-report"))
        posts["order"] = [i for i in keep if posts["posts"][i]["create_at"] <= cutoff]
        tl = server.compose(raw)["timeline"]
        titles = [e["title"] for e in tl]
        self.assertTrue(titles[0].startswith("dev here, implementer role taken"), titles[0])
        self.assertTrue(any(t.startswith("@verifier please verify branch feat/weekly-report") for t in titles))
        self.assertTrue(any("Linux verification is red: 0/3 checks passed" in t for t in titles))
        self.assertTrue(titles[-1].startswith("Merged feat/weekly-report into main"))
        self.assertEqual(sum(1 for e in tl if e["actor"] == "sam"), 1)

    def test_deleted_and_unknown_user_posts_are_skipped(self):
        raw = live_raw()
        posts = raw["mm_posts"]["posts"]
        pid = raw["mm_posts"]["order"][0]
        posts[pid]["delete_at"] = 12345
        raw["mm_users"].pop(posts[raw["mm_posts"]["order"][1]]["user_id"], None)
        server.compose(raw)  # must not raise

    def test_markdown_and_splitting(self):
        self.assertEqual(server.strip_markdown_lines("**Bold** and `code` and [link](http://x) _a_b_\n\n- item *one*\n# Head"),
                         ["Bold and code and link _a_b_", "item one", "Head"])
        self.assertEqual(server.title_and_detail("Short title\nline two\n- bullet"), ("Short title", "line two bullet"))
        long_sentence = "A" * 30 + ". " + "B" * 100
        t, d = server.title_and_detail(long_sentence)
        self.assertEqual((t, d), ("A" * 30 + ".", "B" * 100))
        no_stop = ("word " * 40).strip()
        t, d = server.title_and_detail(no_stop)
        self.assertTrue(t.endswith("\u2026") and len(t) <= server.TITLE_MAX and d.startswith("\u2026"))
        self.assertEqual(server.title_and_detail("   \n  "), ("", ""))
        self.assertEqual(len(server.clip("x" * 500, 220)), 220)


class FakeGateway:
    """Serves the captured responses by path, like the live gateway. `down` simulates an outage."""

    def __init__(self, raw):
        rid = raw["room"]["id"]
        self.routes = {"/gateway/rooms": raw["rooms"], "/gateway/rooms/%s" % rid: raw["room"],
                       "/gateway/rooms/%s/roles" % rid: raw["roles"], "/gateway/agents": raw["agents"],
                       "/gateway/management/controllers": raw["controllers"],
                       "/gateway/rooms/%s/documents" % rid: [
                           {"id": d["id"], "name": d["name"]} for d in raw["documents"].values() if d]}
        for d in raw["documents"].values():
            if d:
                self.routes["/gateway/rooms/%s/documents/%s" % (rid, d["id"])] = d
        self.down = False
        self.calls = []

    def get(self, path):
        self.calls.append(path)
        if self.down:
            raise server.SourceError("GET %s: connection refused" % path)
        return copy.deepcopy(self.routes[path])


class FakeMattermost:
    def __init__(self, raw):
        self.routes = {"/teams/name/switch": {"id": "t1"},
                       "/teams/t1/channels/name/parity-room": raw["mm_channel"],
                       "/channels/%s/posts?per_page=200" % raw["mm_channel"]["id"]: raw["mm_posts"],
                       "/channels/%s/members?per_page=200" % raw["mm_channel"]["id"]: raw["mm_members"]}
        for uid, u in raw["mm_users"].items():
            self.routes["/users/%s" % uid] = u
        self.down = False

    def get(self, path):
        if self.down:
            raise server.SourceError("GET %s: HTTP 503" % path)
        return copy.deepcopy(self.routes[path])


class TestPoller(ContractMixin, unittest.TestCase):
    def setUp(self):
        self.raw = green_same_sha()
        self.gw, self.mm = FakeGateway(self.raw), FakeMattermost(self.raw)
        self.obs = server.Observer(self.gw, self.mm)

    def state(self):
        return json.loads(self.obs.state_bytes())

    def test_starts_pending_then_becomes_verified(self):
        self.assertEqual(self.state()["status"], "pending")
        self.obs.poll_once()
        s = self.state()
        self.assert_valid(s)
        self.assertEqual(s["status"], "verified")
        self.assertTrue(s["timeline"])
        self.assertEqual(self.obs.health()["sources"]["gateway"]["ok"], True)
        self.assertEqual(self.obs.health()["sources"]["mattermost"]["ok"], True)

    def test_outage_keeps_last_good_state_and_recovers(self):
        self.obs.poll_once()
        good = self.state()
        self.gw.down = self.mm.down = True
        self.obs.poll_once()   # must not raise
        s = self.state()
        self.assertEqual(s["status"], "verified")
        self.assertEqual(s["timeline"], good["timeline"])
        h = self.obs.health()
        self.assertFalse(h["sources"]["gateway"]["ok"])
        self.assertIn("connection refused", h["sources"]["gateway"]["error"])
        self.gw.down = self.mm.down = False
        self.obs.poll_once()
        self.assertTrue(self.obs.health()["sources"]["gateway"]["ok"])

    def test_outage_before_first_success_serves_pending(self):
        self.gw.down = self.mm.down = True
        self.obs.poll_once()
        s = self.state()
        self.assert_valid(s)
        self.assertEqual((s["status"], s["timeline"]), ("pending", []))

    def test_room_disappearing_resets_to_pending_and_doc_appearing_is_picked_up(self):
        self.obs.poll_once()
        self.gw.routes["/gateway/rooms"] = [r for r in self.raw["rooms"] if r["name"] != "parity-room"]
        self.obs.poll_once()
        self.assertEqual(self.state()["status"], "pending")
        self.assertEqual(self.state()["room"]["agents"], [])
        # room is back, but matrix-mac has not been written yet
        self.gw.routes["/gateway/rooms"] = self.raw["rooms"]
        rid = self.raw["room"]["id"]
        self.gw.routes["/gateway/rooms/%s/documents" % rid] = [
            {"id": self.raw["documents"]["matrix-linux"]["id"], "name": "matrix-linux"}]
        self.obs.poll_once()
        s = self.state()
        self.assertEqual(s["results"]["mac"]["settings"]["status"], "pending")
        self.assertEqual(s["results"]["linux"]["settings"]["status"], "pass")
        self.assertEqual(s["status"], "pending")

    def test_garbage_responses_never_crash_the_poller(self):
        self.gw.routes["/gateway/rooms"] = {"unexpected": "object"}
        self.obs.poll_once()
        self.mm.routes["/channels/%s/posts?per_page=200" % self.raw["mm_channel"]["id"]] = ["not", "a", "dict"]
        self.obs.poll_once()
        self.assert_valid(self.state())


class TestHTTP(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw = green_same_sha()
        cls.obs = server.Observer(FakeGateway(raw), FakeMattermost(raw))
        cls.obs.poll_once()
        server.Handler.log_message = lambda *a, **k: None   # keep test output quiet
        cls.srv = server.make_server(cls.obs, "127.0.0.1", 0)
        cls.base = "http://127.0.0.1:%d" % cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.srv.server_close()

    def get(self, path, method="GET"):
        req = urllib.request.Request(self.base + path, method=method)
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                return r.status, dict(r.headers), r.read()
        except urllib.error.HTTPError as e:
            try:
                return e.code, dict(e.headers), e.read()
            finally:
                e.close()

    def test_api_state(self):
        code, headers, body = self.get("/api/state")
        self.assertEqual(code, 200)
        self.assertIn("application/json", headers["Content-Type"])
        self.assertEqual(headers["Cache-Control"], "no-store")
        state = json.loads(body)
        self.assertEqual(contract.validate(state).errors, [])
        self.assertEqual(state["status"], "verified")
        self.assertEqual(self.get("/api/state?x=1")[0], 200)
        code, headers, body = self.get("/api/state", "HEAD")
        self.assertEqual((code, body), (200, b""))

    def test_healthz(self):
        code, _, body = self.get("/healthz")
        h = json.loads(body)
        self.assertEqual(code, 200)
        self.assertTrue(h["ok"])
        self.assertEqual(h["status"], "verified")
        self.assertEqual(set(h["sources"]), {"gateway", "mattermost"})

    def test_static_dashboard(self):
        code, _, body = self.get("/")
        self.assertEqual(code, 200)
        self.assertIn(b"<html", body.lower())
        self.assertEqual(self.get("/app.js")[0], 200)
        self.assertEqual(self.get("/fixtures/state-verified.json")[0], 200)

    def test_unknown_and_traversal_and_write_methods(self):
        self.assertEqual(self.get("/api/nope")[0], 404)
        self.assertEqual(self.get("/nope.txt")[0], 404)
        self.assertEqual(self.get("/../observer/server.py")[0], 404)
        self.assertEqual(self.get("/%2e%2e/observer/server.py")[0], 404)
        self.assertEqual(self.get("/..%2fobserver/server.py")[0], 404)
        for m in ("POST", "PUT", "DELETE"):
            code = self.get("/api/state", m)[0]
            self.assertIn(code, (501, 405), m)


if __name__ == "__main__":
    unittest.main(verbosity=2)
