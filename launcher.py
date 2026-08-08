from __future__ import annotations
import hashlib
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV = ROOT / '.venv'
STAMP = VENV / '.f3plus-requirements.sha256'
REQ = ROOT / 'requirements.txt'
MIN_PYTHON = (3, 11)
# Qt Essentials, managed Python, a virtual environment, and native build scratch space.
# The actual install is smaller, but a safety margin prevents partial installs on nearly-full drives.
MIN_SETUP_FREE = 1_500_000_000


def _ensure_visible_windows_console() -> None:
    if os.name != 'nt' or os.environ.get('F3PLUS_CONSOLE_READY') == '1': return
    no_console = sys.stdout is None or sys.stderr is None or Path(sys.executable).name.lower() == 'pythonw.exe'
    if not no_console: return
    python_exe = Path(sys.executable)
    if python_exe.name.lower() == 'pythonw.exe':
        sibling = python_exe.with_name('python.exe')
        if sibling.exists(): python_exe = sibling
    env = os.environ.copy(); env['F3PLUS_CONSOLE_READY'] = '1'
    cmdline = subprocess.list2cmdline([str(python_exe), str(Path(__file__).resolve())])
    subprocess.Popen(['cmd.exe', '/d', '/k', cmdline], cwd=ROOT, env=env)
    raise SystemExit(0)


class _Tee:
    def __init__(self,*streams): self.streams=streams
    def write(self,data):
        for stream in self.streams:
            try: stream.write(data); stream.flush()
            except Exception: pass
        return len(data)
    def flush(self):
        for stream in self.streams:
            try: stream.flush()
            except Exception: pass


def _enable_startup_log():
    try:
        log=open(ROOT/'F3Plus_startup.log','a',encoding='utf-8',buffering=1)
        log.write('\n--- Python launcher started ---\n')
        sys.stdout=_Tee(sys.stdout,log);sys.stderr=_Tee(sys.stderr,log);return log
    except Exception:return None


def _venv_python()->Path:return VENV/('Scripts/python.exe' if os.name=='nt' else 'bin/python')


def _python_runs(py:Path)->bool:
    try:return subprocess.run([str(py),'-c','import sys; raise SystemExit(0 if sys.version_info >= (3,11) else 1)'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=20).returncode==0
    except Exception:return False


def _required_packages_present(py:Path)->bool:
    modules=['PySide6','pynput','pyperclip']+(['Quartz'] if sys.platform=='darwin' else [])
    code='import importlib.util,sys; mods='+repr(modules)+'; missing=[m for m in mods if importlib.util.find_spec(m) is None]; print("\\n".join(missing)); raise SystemExit(1 if missing else 0)'
    try:return subprocess.run([str(py),'-c',code],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=30).returncode==0
    except Exception:return False


def _requirements_hash()->str:
    if not REQ.exists():raise RuntimeError('requirements.txt is missing. Re-extract the complete F3+ ZIP and try again.')
    return hashlib.sha256(REQ.read_bytes()).hexdigest()


def _check_python():
    if sys.version_info<MIN_PYTHON:
        found=f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}'
        raise RuntimeError(f'Python {found} was found, but F3+ requires Python 3.11 or newer.')


def _gb(n:int)->str:return f'{n/1024**3:.2f} GB'


def _setup_locations():
    locations=[]
    for raw in (ROOT,tempfile.gettempdir(),Path.home()):
        try:p=Path(raw).resolve();anchor=p.anchor or str(p)
        except Exception:continue
        if any(x[0]==anchor for x in locations):continue
        try:free=shutil.disk_usage(p).free
        except Exception:continue
        locations.append((anchor,free,p))
    return locations


def _preflight_disk_space():
    low=[(anchor,free,p) for anchor,free,p in _setup_locations() if free<MIN_SETUP_FREE]
    if not low:return
    lines=[f'{anchor or p}: {_gb(free)} free' for anchor,free,p in low]
    raise RuntimeError(
        'F3+ needs more free disk space before first-run package setup. '
        f'Keep at least {_gb(MIN_SETUP_FREE)} free on the drive used by F3+ and your temporary/cache folder.\n'
        'Low-space location(s):\n - '+'\n - '.join(lines)+'\n\n'
        'Free space or move the extracted F3+ folder to a drive with more room, then run START_F3PLUS again.'
    )


def _failure_kind(output:str)->str:
    low=output.lower()
    if any(x in low for x in ('no space left on device','not enough space on the disk','there is not enough space on the disk','os error 112','errno 28')):return 'disk'
    if any(x in low for x in ('certificate verify failed','certificate_verify_failed','tls','ssl','connection reset','connection timed out','temporary failure in name resolution','could not resolve host')):return 'network'
    if any(x in low for x in ('access is denied','permission denied','winerror 5')):return 'permission'
    if any(x in low for x in ('no matching distribution found','not a supported wheel','unsupported platform')):return 'compatibility'
    return 'other'


def _run_visible(cmd:list[str],*,label:str,attempts:int=1)->tuple[int,str]:
    combined=[]
    for attempt in range(1,attempts+1):
        print(f'      {label}'+(f' (attempt {attempt}/{attempts})' if attempts>1 else ''))
        print('      Command: '+subprocess.list2cmdline(cmd))
        lines=[]
        try:
            proc=subprocess.Popen(cmd,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace',bufsize=1)
            assert proc.stdout is not None
            for line in proc.stdout:
                clean=line.rstrip();lines.append(clean);print('      '+clean)
            rc=proc.wait()
        except OSError as exc:
            lines.append(str(exc));print(f'      Could not start command: {exc}');rc=127
        combined.extend(lines)
        if rc==0:return 0,'\n'.join(combined)
        kind=_failure_kind('\n'.join(lines));print(f'      Command failed with exit code {rc}.')
        if kind=='disk':
            print('      Disk space is exhausted; retrying the same install would only fail again.')
            break
        if attempt<attempts:print('      Retrying in 2 seconds...');time.sleep(2)
    return rc,'\n'.join(combined)


def _disk_error_message()->str:
    spots=_setup_locations();summary=', '.join(f'{a}: {_gb(f)} free' for a,f,_ in spots) or 'free-space check unavailable'
    return (
        'Package setup stopped because the disk ran out of free space. No further retries were attempted.\n'
        f'Current free space: {summary}.\n'
        f'Free at least {_gb(MIN_SETUP_FREE)} on the affected drive, or move F3+ to a roomier drive, then run START_F3PLUS again. '
        'F3+ uses the smaller PySide6-Essentials package, but Qt still needs working room while it extracts.'
    )


def _pip_install(py:Path,*,force_repair:bool=False):
    _preflight_disk_space()
    upgrade=[str(py),'-m','pip','install','--disable-pip-version-check','--no-cache-dir','--index-url','https://pypi.org/simple','--upgrade','pip','setuptools','wheel']
    rc,out=_run_visible(upgrade,label='Checking Python packaging tools...',attempts=2)
    if rc!=0:
        if _failure_kind(out)=='disk':raise RuntimeError(_disk_error_message())
        print('      Packaging-tool update was unavailable; continuing with the installed pip.')
    install=[str(py),'-m','pip','install','--disable-pip-version-check','--no-cache-dir','--index-url','https://pypi.org/simple','--prefer-binary','--only-binary',':all:','--retries','5','--timeout','45']
    if force_repair:install += ['--upgrade','--force-reinstall']
    install += ['-r',str(REQ)]
    rc,out=_run_visible(install,label='Installing F3+ interface/input packages...',attempts=2)
    if rc!=0 and _failure_kind(out)=='disk':raise RuntimeError(_disk_error_message())
    if rc!=0:
        uv_name='uv.exe' if os.name=='nt' else 'uv';uv_root=ROOT/'.runtime'/'uv';uv=next((x for x in uv_root.rglob(uv_name) if x.is_file()),None) if uv_root.exists() else None
        if uv is not None:
            fallback=[str(uv),'pip','install','--no-cache','--python',str(py),'--index-url','https://pypi.org/simple','-r',str(REQ)]
            print('      pip could not complete setup; trying the project-local uv installer as a fallback.')
            rc,out2=_run_visible(fallback,label='Installing packages with uv...',attempts=2);out+='\n'+out2
            if rc!=0 and _failure_kind(out2)=='disk':raise RuntimeError(_disk_error_message())
    if rc!=0:
        kind=_failure_kind(out)
        if kind=='network':reason='The package index connection failed. Check firewall/TLS/security software and access to pypi.org.'
        elif kind=='permission':reason='Windows/macOS/Linux denied access to a setup file. Move F3+ to a normal writable folder and try again.'
        elif kind=='compatibility':reason='A pinned runtime package is not available for this Python/OS combination.'
        else:reason='Read the first ERROR line above for the failing package or system error.'
        raise RuntimeError('Python package installation failed. '+reason+' Full output is saved in F3Plus_startup.log.')


def ensure_environment()->Path:
    _check_python();py=_venv_python()
    if VENV.exists() and (not py.exists() or not _python_runs(py)):
        print('[1/3] Existing private environment is incomplete or no longer usable. Recreating it...');shutil.rmtree(VENV,ignore_errors=True)
    if not py.exists():
        _preflight_disk_space();print("[1/3] Creating F3+'s private Python environment...");venv.EnvBuilder(with_pip=True,clear=False,symlinks=False).create(VENV)
    else:print('[1/3] Private Python environment is ready.')
    try:pip_probe=subprocess.run([str(py),'-m','pip','--version'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    except OSError as exc:raise RuntimeError(f'F3+ could not run its private Python environment: {exc}') from exc
    if pip_probe.returncode!=0:
        print('      Repairing pip in the private environment...');rc,_=_run_visible([str(py),'-m','ensurepip','--upgrade'],label='Bootstrapping pip...')
        if rc!=0:raise RuntimeError('F3+ created its private environment, but pip could not be prepared. See the startup log for details.')
    wanted=_requirements_hash();have=STAMP.read_text(encoding='utf-8').strip() if STAMP.exists() else '';packages_ready=_required_packages_present(py)
    if have!=wanted or not packages_ready:
        print('[2/3] A required package is missing or damaged. Repairing the private environment...' if have==wanted and not packages_ready else '[2/3] Installing required interface and input packages...')
        print('      First run requires internet access. F3+ checks free space before the Qt install and does not cache the wheels.')
        _pip_install(py,force_repair=(have==wanted and not packages_ready))
        if not _required_packages_present(py):raise RuntimeError('Package installation completed, but one or more required modules are still unavailable. See F3Plus_startup.log for complete output.')
        STAMP.write_text(wanted+'\n',encoding='utf-8')
    else:print('[2/3] Required Python packages are already installed.')
    return py


def prepare_native_dependencies()->list[str]:
    warnings=[];print('[3/3] Preparing Minecraft calculation components...')
    try:
        from minescript.seed.bundled import build_cubiomes,bedrock_status
        try:build_cubiomes();print('      Cubiomes is ready.')
        except Exception as exc:warnings.append('Cubiomes could not be prepared. Seed/biome tools that depend on it may be unavailable until setup succeeds. Details: '+str(exc))
        print('      Nether Bedrock Cracker is ready.' if bedrock_status().executable else '      Nether Bedrock Cracker will be prepared when seed recovery is first opened.')
    except Exception as exc:warnings.append('Optional Minecraft components were not fully prepared. Details: '+str(exc))
    return warnings


def main()->int:
    _ensure_visible_windows_console();_enable_startup_log()
    try:in_project_venv=Path(sys.prefix).resolve()==VENV.resolve()
    except Exception:in_project_venv=False
    if in_project_venv or os.environ.get('F3PLUS_BOOTSTRAPPED')=='1':return subprocess.call([sys.executable,str(ROOT/'main.py')],cwd=ROOT)
    print('F3+ first-run setup',flush=True);print(f'Using Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}\n')
    try:
        py=ensure_environment();warnings=prepare_native_dependencies()
        if warnings:
            print('\nSetup completed with warnings:')
            for w in warnings:print(' - '+w)
            print('\nF3+ will open now. Features unrelated to those warnings remain available.')
    except Exception as exc:
        print('\nSETUP COULD NOT FINISH',flush=True);print(str(exc),flush=True);traceback.print_exc();return 2
    print('\nOpening F3+...',flush=True);env=os.environ.copy();env['F3PLUS_BOOTSTRAPPED']='1';return subprocess.call([str(py),str(ROOT/'main.py')],cwd=ROOT,env=env)


if __name__=='__main__':raise SystemExit(main())
