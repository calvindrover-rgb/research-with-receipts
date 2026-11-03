"""Sandbox runners. Each task gets a fresh, throwaway environment that is destroyed afterward.
docker: --rm, no secrets, read-only rootfs, non-root, 256MB, 0.5 CPU, pids cap, no caps, egress only via allowlist proxy.
local:  subprocess fallback for dev/tests: scrubbed env, rlimits, timeout, temp dir deleted."""
import os, json, subprocess, tempfile, shutil, sys, resource
HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(os.path.dirname(HERE), "sandbox")
TIMEOUT = int(os.environ.get("SANDBOX_TIMEOUT", "45"))

def _parse(stdout, stderr, code, killed=False):
    out = {"exit_code": code, "stdout": stdout[-6000:], "stderr": stderr[-4000:], "timed_out": killed, "result": None, "receipts": []}
    for line in stdout.splitlines():
        if line.startswith("@@RESULT@@"):
            d = json.loads(line[10:]); out["result"], out["receipts"] = d["result"], d["receipts"]
    out["stdout"] = "\n".join(l for l in out["stdout"].splitlines() if not l.startswith("@@RESULT@@"))
    return out

def run_docker(code):
    cmd = ["docker", "run", "--rm", "-i", "--network", os.environ.get("SANDBOX_NETWORK", "sandbox_net"),
           "--read-only", "--tmpfs", "/tmp:size=32m", "--memory", "256m", "--cpus", "0.5", "--pids-limit", "64",
           "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
           "-e", "HTTPS_PROXY=http://egress-proxy:3128", "-e", "https_proxy=http://egress-proxy:3128",
           os.environ.get("SANDBOX_IMAGE", "pra-sandbox:latest")]
    if os.environ.get("SANDBOX_RUNTIME"): cmd[3:3] = ["--runtime", os.environ["SANDBOX_RUNTIME"]]  # e.g. runsc (gVisor)
    try:
        p = subprocess.run(cmd, input=code, capture_output=True, text=True, timeout=TIMEOUT)
        return _parse(p.stdout, p.stderr, p.returncode)
    except subprocess.TimeoutExpired as e:
        return _parse(e.stdout or "", (e.stderr or "") + "\nKILLED: time limit", -9, True)

def _limits():
    resource.setrlimit(resource.RLIMIT_AS, (512 * 2**20,) * 2)
    resource.setrlimit(resource.RLIMIT_CPU, (TIMEOUT,) * 2)
    os.setsid()

def run_local(code):
    d = tempfile.mkdtemp(prefix="pra-")
    try:
        f = os.path.join(d, "task.py"); open(f, "w").write(code)
        env = {"PATH": "/usr/bin:/bin", "PYTHONPATH": LIB, "HOME": d}  # no secrets pass through
        try:
            p = subprocess.run([sys.executable, "-I", "-c", f"import sys; sys.path.insert(0,{LIB!r}); exec(open({f!r}).read())"],
                               capture_output=True, text=True, timeout=TIMEOUT, cwd=d, env=env, preexec_fn=_limits)
            return _parse(p.stdout, p.stderr, p.returncode)
        except subprocess.TimeoutExpired as e:
            return _parse((e.stdout or b"").decode() if isinstance(e.stdout, bytes) else (e.stdout or ""), "KILLED: time limit", -9, True)
    finally:
        shutil.rmtree(d, ignore_errors=True)  # lifecycle: destroy after each task

def run(code):
    return run_docker(code) if os.environ.get("SANDBOX_MODE", "local") == "docker" else run_local(code)
