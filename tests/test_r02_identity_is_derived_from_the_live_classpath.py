"""R-2 — what each stack claims to be, checked against what actually resolved at runtime.

Verification reads the running process's own resolved classpath or dependency tree.
Build files and the host toolchain are not inputs: a pom can declare anything, and what
matters is what the JVM loaded.

The identity endpoint is instrumentation, not contract. It reports resolved runtime
*data* — versions, the artifact set, the concrete HTTP server class — and never a
claimed identity string, because a module asserting its own identity is not proof of
anything. Identity is therefore derived here, from the artifact set, against
`required_artifacts` and `forbidden_artifacts` in the manifest.

The contrast this repository exists to make depends on absence as much as presence:
"traditional Spring" means nothing unless no Boot artifact is on that classpath.
"""

from __future__ import annotations

import re

import pytest

import spine

REQUIRED_REPORT_FIELDS = ("runtime_version", "artifacts", "http_server_class")
JDK_HTTP_MODULE = "jdk.httpserver"


def _report(sid: str, stack: dict) -> dict:
    response = spine.http_get(spine.identity_url(sid, stack))
    assert response.status_code == 200, (
        f"stack '{sid}' identity endpoint returned {response.status_code}"
    )
    try:
        doc = response.json()
    except ValueError:
        pytest.fail(f"stack '{sid}' identity endpoint did not return JSON")
    for field in REQUIRED_REPORT_FIELDS:
        if field not in doc:
            pytest.fail(f"stack '{sid}' identity report omits '{field}'")
    return doc


def _names_match(artifact: str, needle: str, rule: str) -> bool:
    """Whether an artifact is the named dependency, under the stack's declared rule.

    Substring matching made the forbidden entry "react" match "react-is", a transitive
    dependency of the Angular toolchain that is not React — matching on presence where
    the rule is about identity.

    Tightening it to a name boundary then broke the JVM side, where "spring-boot" is
    meant to forbid the whole family including spring-boot-autoconfigure. The two
    ecosystems mean different things by a dependency name, so the manifest says which:

      prefix  a family — the Maven coordinate style, where spring-boot covers every
              spring-boot-* artifact on the classpath
      exact   one package — the npm style, where react and react-is are unrelated
    """
    if rule == "exact":
        # rsplit, not split: a scoped package name begins with @, so splitting on the
        # first one yields an empty name and silently matches nothing.
        return artifact.rsplit("@", 1)[0] == needle
    if rule == "prefix":
        return artifact.startswith(needle)
    raise AssertionError(f"unknown artifact_match rule {rule!r}")


def _version_tuple(value: str) -> tuple[int, ...]:
    parts = re.findall(r"\d+", str(value))
    return tuple(int(p) for p in parts[:3]) or (0,)


def test_the_manifest_declares_derivable_identity_rather_than_a_label():
    """Identity is derived from resolved artifacts, so the manifest must declare them."""
    incomplete = []
    for sid, stack in sorted(spine.active_stacks().items()):
        if not stack.get("runtime_version_floor"):
            incomplete.append(f"'{sid}' declares no runtime_version_floor")
        if "required_artifacts" not in stack:
            incomplete.append(
                f"'{sid}' declares no required_artifacts; identity must be derivable from "
                "the resolved artifact set rather than from a claimed label"
            )
        if "forbidden_artifacts" not in stack:
            incomplete.append(
                f"'{sid}' declares no forbidden_artifacts; the contrast depends on what is "
                "absent as much as on what is present"
            )
        if "framework_artifact" not in stack:
            incomplete.append(
                f"'{sid}' declares no framework_artifact; declare the artifact and its "
                "floor, or declare it as none with the reason. An absent declaration is "
                "what let two frontends sit on superseded majors unnoticed"
            )
    assert not incomplete, (
        "manifest entries must support derived identity:\n  " + "\n  ".join(incomplete)
    )


@pytest.mark.needs_stacks
def test_every_active_stack_reports_healthy_and_answers_for_a_reason():
    for sid, stack in sorted(spine.active_stacks().items()):
        cid, _ = spine.container_identity(stack["service"])
        import subprocess
        res = subprocess.run(
            ["docker", "inspect", "-f", "{{.State.Health.Status}}{{.State.Status}}", cid],
            capture_output=True, text=True, timeout=30,
        )
        status = res.stdout.strip()
        assert "healthy" in status or status.endswith("running"), (
            f"stack '{sid}' container {cid[:12]} is not healthy (state: {status or 'unknown'})"
        )
        response = spine.http_get(spine.health_url(sid, stack))
        assert response.status_code == 200, (
            f"stack '{sid}' health endpoint returned {response.status_code}"
        )

        # The status is not the evidence. A frontend's entry surface is "/", and a
        # single-page app answers that path — and every other path — with its document,
        # whatever state the application is in. So read what came back: a backend says it
        # is up, and a frontend's document references the bundle it was built with.
        body = response.text
        assert body.strip(), f"stack '{sid}' health endpoint returned an empty body"

        if stack.get("role") == "frontend":
            assert re.search(r"src=[\"'][^\"']*assets[^\"']+\.js", body), (
                f"stack '{sid}' served a document referencing no built bundle. A "
                "single-page app answers any path with its document, so a 200 here says "
                "only that a server is listening."
            )
        else:
            # The endpoint has to be a real endpoint. A server that answers everything the
            # same way tells you nothing by answering this, so ask it something it should
            # not recognise and require a different answer.
            nonsense = spine.http_get(spine.base_url(sid, stack) + "/__no_such_path")
            assert (nonsense.status_code, nonsense.text) != (response.status_code, body), (
                f"stack '{sid}' answers an unknown path exactly as it answers its health "
                "endpoint, so a 200 there is evidence of nothing"
            )


@pytest.mark.needs_stacks
def test_the_identity_endpoint_reports_data_and_never_a_claimed_identity():
    """A module asserting its own identity is not proof."""
    offenders = []
    for sid, stack in sorted(spine.active_stacks().items()):
        doc = _report(sid, stack)
        claimed = sorted(k for k in doc if k.lower() in spine.CLAIMED_IDENTITY_KEYS)
        if claimed:
            offenders.append(
                f"'{sid}' identity report carries self-asserted key(s): {', '.join(claimed)}"
            )
        if not isinstance(doc.get("artifacts"), list):
            offenders.append(
                f"'{sid}' reports no resolved artifact set; there is nothing to derive "
                "identity from"
            )
    assert not offenders, (
        "instrumentation reports resolved data, never a claimed identity:\n  "
        + "\n  ".join(offenders)
    )


@pytest.mark.needs_stacks
def test_the_reported_runtime_satisfies_the_declared_floor():
    for sid, stack in sorted(spine.active_stacks().items()):
        floor = spine.stack_field(sid, stack, "runtime_version_floor")
        reported = _report(sid, stack)["runtime_version"]
        assert _version_tuple(reported) >= _version_tuple(floor), (
            f"stack '{sid}' reports runtime {reported}, below declared floor {floor}"
        )


@pytest.mark.needs_stacks
def test_required_artifacts_resolve_on_the_runtime_classpath():
    """Framework identity is the artifact set that actually resolved, not a label."""
    missing = []
    for sid, stack in sorted(spine.active_stacks().items()):
        required = stack.get("required_artifacts") or []
        if not required:
            continue
        artifacts = [str(a).lower() for a in _report(sid, stack)["artifacts"]]
        rule = str(stack.get("artifact_match", "prefix"))
        for needle in (str(r).lower() for r in required):
            if not any(_names_match(a, needle, rule) for a in artifacts):
                missing.append(
                    f"'{sid}' declares required artifact '{needle}' which does not resolve "
                    "at runtime; the stack is not the thing the manifest says it is"
                )
    assert not missing, (
        "declared identity is not borne out by the runtime classpath:\n  "
        + "\n  ".join(missing)
    )


@pytest.mark.needs_stacks
def test_forbidden_artifacts_are_absent_from_the_runtime_classpath():
    """Traditional Spring: no Boot, no auto-configuration. The language modules: no web
    framework at all.

    This is the half that makes the pair a contrast rather than a label. Presence can be
    faked by a dependency someone added for an unrelated reason; absence cannot.
    """
    hits = []
    for sid, stack in sorted(spine.active_stacks().items()):
        forbidden = stack.get("forbidden_artifacts") or []
        if not forbidden:
            continue
        artifacts = [str(a).lower() for a in _report(sid, stack)["artifacts"]]
        rule = str(stack.get("artifact_match", "prefix"))
        for needle in (str(f).lower() for f in forbidden):
            for artifact in artifacts:
                if _names_match(artifact, needle, rule):
                    hits.append(f"'{sid}': forbidden '{needle}' resolved as '{artifact}'")
    assert not hits, (
        "stacks resolve artifacts they declare forbidden; the contrast they exist to "
        "make is falsified:\n  " + "\n  ".join(hits)
    )


@pytest.mark.needs_stacks
def test_the_modern_java_http_surface_resolves_to_the_jdk_module():
    """No web framework: the concrete server class is the JDK's, reported as data."""
    candidates = {
        sid: s for sid, s in spine.active_stacks().items()
        if s.get("tier") == "LANGUAGE" and s.get("language") == "java"
    }
    if not candidates:
        pytest.fail(
            "no active LANGUAGE-tier java stack in the manifest; the framework-free Java "
            "lane is half of the language pair and must be declared"
        )
    for sid, stack in sorted(candidates.items()):
        doc = _report(sid, stack)
        # The module, not the package. The running class is
        # sun.net.httpserver.HttpServerImpl, which is that module's implementation of
        # com.sun.net.httpserver.HttpServer — asserting on the API package name would
        # reject the correct answer.
        module = str(doc.get("http_server_module", ""))
        server_class = str(doc["http_server_class"])
        assert module == JDK_HTTP_MODULE, (
            f"stack '{sid}' serves HTTP from module '{module}' (class {server_class}); "
            f"this lane requires {JDK_HTTP_MODULE} and forbids substitution"
        )


def test_instrumentation_endpoints_are_declared_in_the_manifest():
    """Declared, so the contract and every other consumer can exclude them by reading."""
    declared = spine.instrumentation_paths()
    assert declared, (
        "no instrumentation endpoints declared in the manifest; the identity and "
        "autoconfig checks have nothing to read and contract parity has nothing to exclude"
    )
    for sid, stack in sorted(spine.active_stacks().items()):
        if not stack.get("identity_endpoint"):
            pytest.fail(f"active stack '{sid}' declares no identity_endpoint")


# --- framework and servlet-container floors ------------------------------------
#
# The runtime version and the *presence* of framework artifacts were checked here long
# before their versions were. Two frontends therefore sat on an end-of-life Angular major
# and a superseded React major, and nothing in the suite could have said so: floors were
# declared for the runtimes only, so the frameworks were an unchecked default.
#
# The floor is declared per stack in the manifest. The version is read from the artifact
# the running process resolved, never from a build file or a lockfile.

VERSION_IN_JAR = re.compile(r"-(\d+(?:\.\d+)*)(?:\.[A-Za-z][\w.]*)?\.jar$")
VERSION_IN_NPM = re.compile(r"@(\d+(?:\.\d+)*)")


def _as_tuple(version: str) -> tuple:
    return tuple(int(part) for part in version.split(".") if part.isdigit())


def _resolved_version(artifacts, wanted: str):
    """The version of one resolved artifact, whichever coordinate style it uses."""
    for entry in artifacts:
        if entry.startswith(f"{wanted}@"):
            found = VERSION_IN_NPM.search(entry[len(wanted):])
            if found:
                return entry, found.group(1)
        name = entry.rsplit("/", 1)[-1]
        if name.startswith(f"{wanted}-"):
            found = VERSION_IN_JAR.search(name)
            if found:
                return entry, found.group(1)
    return None, None


def _floor_checks(stack_id: str, stack: dict):
    """(label, artifact, floor) for every version floor this stack declares."""
    for label, artifact_key, floor_key in (
        ("framework", "framework_artifact", "framework_version_floor"),
        ("servlet container", "servlet_container_artifact", "servlet_container_version_floor"),
    ):
        artifact = stack.get(artifact_key)
        if not artifact or artifact == "none":
            continue
        floor = stack.get(floor_key)
        if not floor:
            pytest.fail(
                f"MALFORMED INPUT: stack '{stack_id}' declares {artifact_key} but no "
                f"{floor_key}; an artifact with no floor is the gap this closes"
            )
        yield label, str(artifact), str(floor)


@pytest.mark.needs_stacks
def test_resolved_framework_versions_meet_their_declared_floors():
    below, unresolved = [], []
    for sid, stack in sorted(spine.active_stacks().items()):
        artifacts = _report(sid, stack).get("artifacts") or []
        for label, artifact, floor in _floor_checks(sid, stack):
            entry, version = _resolved_version(artifacts, artifact)
            if not version:
                unresolved.append(f"{sid}: {label} '{artifact}' resolves nothing at runtime")
                continue
            if _as_tuple(version) < _as_tuple(floor):
                below.append(
                    f"{sid}: {label} {artifact} is {version}, below the declared floor "
                    f"{floor} (resolved as {entry})"
                )

    assert not unresolved, (
        "declared artifacts that the running process does not resolve:\n  "
        + "\n  ".join(unresolved)
    )
    assert not below, (
        "resolved versions below their declared floor. The floor is the supported "
        "release; running under it is the defect, not the floor:\n  " + "\n  ".join(below)
    )
