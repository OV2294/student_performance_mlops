# 🎓 Student Performance Prediction — MLOps Pipeline

Predicts whether a student will **pass or fail**, wrapped in a reproducible, automated MLOps pipeline.
**Jenkins CI/CD runs on Windows** (every Jenkins step is a `bat`/cmd command). All commands below are for
**Windows 10/11 — Command Prompt (cmd)** unless marked *PowerShell*.

| Requirement | Tool | File |
|---|---|---|
| Reproducible pipeline + data versioning | DVC + Git | `dvc.yaml`, `params.yaml`, `dvc.lock` |
| Experiment tracking | MLflow | `src/train.py` |
| Workflow automation / scheduling | Jenkins (nightly cron + poll SCM) | `Jenkinsfile` |
| Model serving | FastAPI | `src/api.py` |
| Deployment | Docker + docker compose | `Dockerfile`, `docker-compose.yml` |
| Monitoring | PSI drift, API metrics, prediction log | `src/monitor.py` |
| UI | Streamlit | `app.py` |

```
generate_data ─▶ preprocess ─▶ train (MLflow) ─▶ evaluate (quality gate) ─▶ monitor (drift)
                                    └─▶ models\model.joblib ─▶ FastAPI :8000 ─▶ Streamlit :8501
Jenkins: checkout ▶ .venv ▶ tests ▶ dvc repro ▶ tests ▶ drift ▶ docker build ▶ compose up ▶ smoke test
```

---
## ⚡ QUICK START (PowerShell, inside the project folder)

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt

git init
dvc init
dvc cache dir --local C:\dvc_cache
dvc repro
```
*(PowerShell blocks activation? run once: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`)*

* `dvc cache dir --local C:\dvc_cache` keeps DVC's cache path short, so `dvc repro` works even if the project is
  inside a deep/long Desktop folder (Windows 260-character limit).
* Or do all of it in one go: `scripts\first_run.bat`
* Result: `reports\metrics.json`, `models\model.joblib`, `mlflow.db`, `dvc.lock`.
* Then: `streamlit run app.py`  •  `mlflow ui --backend-store-uri sqlite:///mlflow.db`  •  `uvicorn src.api:app --port 8000`

---
## STEP 0 — Install prerequisites (once)

Open **cmd as Administrator** and use winget (built into Windows 10/11):
```bat
winget install -e --id Python.Python.3.11 --scope machine
winget install -e --id Git.Git
winget install -e --id Docker.DockerDesktop
winget install -e --id EclipseAdoptium.Temurin.17.JDK
winget install -e --id Jenkins.Jenkins
```
* Restart the PC after Docker Desktop (it enables WSL2). Start Docker Desktop and wait for "Engine running".
* If `winget install Jenkins.Jenkins` is unavailable, download the **Windows .msi** from https://www.jenkins.io/download/.
* Python must be installed **for all users** (`--scope machine` above, or tick "Install for all users" + "Add to PATH"
  in the installer) so the Jenkins service can find it.

Open a **new** cmd window and verify:
```bat
cd student-performance-mlops
scripts\check_prereqs.bat
```

---
## STEP 1 — Run the project locally

```bat
cd student-performance-mlops

python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
```
*(PowerShell: if activation is blocked run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once.)*

Initialise Git + DVC and run the whole pipeline:
```bat
git init
dvc init
dvc cache dir --local C:\dvc_cache
dvc repro
```
Expected: 5 stages run (`generate_data`, `preprocess`, `train`, `evaluate`, `monitor`), then
`reports\metrics.json`, `models\model.joblib`, `mlflow.db`, `dvc.lock` exist. `Quality gate passed.` is printed.


### ⚠️ Windows "path too long" / `[Errno 2] No such file or directory ... .dvc\cache\runs\...tmp`
Windows limits full paths to 260 characters and DVC's cache filenames are ~130 characters long. If the project sits deep
inside `Desktop\...` (or a folder with a long name, or nested twice), `dvc repro` fails right after the first stage.
**Fix: keep the project in a short path with no spaces**, e.g. `C:\mlops\sp`, and recreate the .venv there
(virtual environments are not movable). Optionally enable long paths (PowerShell as Administrator, then reboot):
```powershell
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
git config --system core.longpaths true
```

Useful checks:
```bat
dvc dag
dvc metrics show
python -m pytest tests -q
python -m src.monitor --simulate
```

Start the services (each in its **own** cmd window, with `.venv\Scripts\activate` first):
```bat
mlflow ui
uvicorn src.api:app
streamlit run app.py
```
| Service | URL |
|---|---|
| MLflow UI | http://localhost:5000 |
| FastAPI docs | http://localhost:8000/docs |
| Streamlit | http://localhost:8501 |

Test the API from cmd (Windows 10+ ships `curl.exe`):
```bat
curl http://localhost:8000/health
python scripts\smoke_test.py http://localhost:8000
```

Re-run an experiment: change e.g. `n_estimators` in `params.yaml`, then `dvc repro` — only affected stages
re-run and a new MLflow run appears.

---
## STEP 2 — Push to GitHub

1. On github.com → **New repository** → name `student-performance-mlops` → **do not** add README/.gitignore → Create.
2. In cmd (project folder, after `dvc repro`):
```bat
git config --global user.name "Your Name"
git config --global user.email "you@example.com"

git add .
git status
git commit -m "Student performance MLOps pipeline"
git branch -M main
git remote add origin https://github.com/<your-username>/student-performance-mlops.git
git push -u origin main
```
3. When asked to log in, use your GitHub username and a **Personal Access Token** as the password
   (GitHub → Settings → Developer settings → Personal access tokens → *Tokens (classic)* → scope `repo`).
   A browser sign-in popup from Git Credential Manager also works.

`dvc.lock`, `.dvc\`, `dvc.yaml`, `params.yaml` get committed; the raw data and model files are DVC-managed,
so Jenkins regenerates them with `dvc repro`.

**Optional — DVC remote storage (data versioning proof for viva):**
```bat
mkdir C:\dvc_storage
dvc remote add -d localstore C:\dvc_storage
dvc push
git add .dvc\config
git commit -m "Add DVC remote"
git push
```
> Note: Jenkins runs `dvc repro --force`, so it does **not** need the remote.

---
## STEP 3 — Docker deployment (manual)

Docker Desktop must be running. Run the pipeline first (Step 1) so `models\model.joblib` and `mlflow.db` exist.
```bat
docker compose up -d --build
docker compose ps
docker compose logs -f api
```
API http://localhost:8000/docs • Dashboard http://localhost:8501 • MLflow http://localhost:5000

Stop everything: `docker compose down`
> Stop your local `uvicorn`/`streamlit`/`mlflow ui` windows first (Ctrl+C) — the containers use the same ports.

---
## STEP 4 — Jenkins CI/CD on Windows

### 4.1 Make Jenkins run as YOUR Windows user (needed for Docker Desktop)
Jenkins installs as a service running as *Local System*, which cannot talk to Docker Desktop. Change it:

*GUI:* press `Win+R` → `services.msc` → **Jenkins** → Properties → **Log On** → *This account* → enter your
Windows username (`.\yourname`) and password → OK.

*or cmd (Administrator):*
```bat
sc config Jenkins obj= ".\yourname" password= "your-windows-password"
```
Restart the service (cmd as Administrator):
```bat
net stop Jenkins
net start Jenkins
sc query Jenkins
```
(Windows accounts without a password can't be used for services — set a password for your Windows user first.)

### 4.2 First-time setup
```bat
type C:\ProgramData\Jenkins\.jenkins\secrets\initialAdminPassword
```
Open http://localhost:8080 → paste the password → **Install suggested plugins** → create admin user → Save.
(If port 8080 is busy, change it in `C:\Program Files\Jenkins\jenkins.xml` → `--httpPort=` → restart service.)

Check the plugins **Git**, **Pipeline**, **JUnit** are installed (Manage Jenkins → Plugins → Installed) — the
suggested set includes them.

### 4.3 Create the pipeline job
1. Dashboard → **New Item** → name `student-performance-mlops` → **Pipeline** → OK.
2. **Build Triggers**: leave empty — the schedule is already inside the `Jenkinsfile`
   (it is applied after the first build).
3. **Pipeline** section → Definition: **Pipeline script from SCM**
   * SCM: **Git**
   * Repository URL: `https://github.com/<your-username>/student-performance-mlops.git`
   * Credentials: *Add* → Username with password → GitHub username + Personal Access Token
     (only needed if the repo is private)
   * Branch: `*/main`
   * Script Path: `Jenkinsfile`
4. **Save** → **Build Now**.

Watch it: click the build number (#1) → **Console Output**. First build takes ~10 min (installs packages, builds image).

### 4.4 What the pipeline does (Jenkinsfile)
| Stage | Windows command run |
|---|---|
| Checkout | `checkout scm` |
| Setup Python env | `python -m venv .venv` + `pip install -r requirements-dev.txt` |
| Unit tests | `.venv\Scripts\python -m pytest tests` |
| Data + Train (DVC) | `dvc init` (if needed) + `dvc repro --force` |
| Quality gate & tests | pytest again, now with the trained model |
| Drift monitoring | `python -m src.monitor` |
| Docker build | `docker build -t student-performance-mlops:<build#> .` |
| Deploy | `docker compose down` + `docker compose up -d` |
| Smoke test | `python scripts\smoke_test.py http://localhost:8000` |

### 4.5 Scheduling / automation (already in the Jenkinsfile)
```groovy
triggers {
    cron('H 2 * * *')          // nightly retrain ≈ 02:00  → workflow scheduling
    pollSCM('H/5 * * * *')     // checks GitHub every ~5 min; new commit → auto build → CI/CD
}
```
Test the automation: change something (e.g. `n_estimators: 250` in `params.yaml`), then
```bat
git add .
git commit -m "Tune random forest"
git push
```
Within ~5 minutes a new build starts on its own, retrains, and redeploys. Check http://localhost:8501 afterwards.
To see the scheduled trigger fire without waiting: Job → **Configure** → confirm the trigger shows under *Build Triggers*
after build #1, or temporarily set `cron('H/2 * * * *')`.

### 4.6 Troubleshooting
| Error in Console Output | Fix |
|---|---|
| `'python' is not recognized` | Python not on **system** PATH / installed only for your user. Reinstall for all users, then `net stop Jenkins` & `net start Jenkins`. |
| `'docker' is not recognized` or `error during connect ... dockerDesktopLinuxEngine` | Start Docker Desktop and wait for "Engine running"; make sure Jenkins service runs as your user (4.1). |
| `'git' is not recognized` / `dvc: not found` | Restart Jenkins service after installing Git; `dvc` comes from the .venv (Jenkinsfile puts `.venv\Scripts` on PATH). |
| `port is already allocated` (8000/8501/5000) | A local `uvicorn`/`streamlit`/`mlflow ui` is still running — close it, or run `docker compose down`. |
| `ImportError: cannot import name 'FallbackAsyncAdaptedQueuePool' from 'sqlalchemy.pool'` | MLflow needs SQLAlchemy 2.0.x; SQLAlchemy 2.1 breaks it. Run `pip install "sqlalchemy>=2.0.30,<2.1"` (already pinned in `requirements.txt`). |
| `Quality gate FAILED` | Model F1/ROC-AUC below threshold in `src/evaluate.py` — tune `params.yaml`. |
| `Authentication failed` on checkout | Wrong/expired GitHub token in Jenkins credentials (private repo). |
| `pytest` API test returns 503 | Only in the first test stage (model not trained yet on a clean workspace) — see note below. |

> **Note on the first test stage:** on a brand-new workspace the model doesn't exist yet, so the API test accepts a
> `503` there and is re-run after training in the *Quality gate & tests* stage.

### 4.7 Optional — instant builds via GitHub webhook
Poll SCM is enough for a college demo. For instant builds you need a public URL for your PC:
```bat
winget install -e --id Ngrok.Ngrok
ngrok http 8080
```
GitHub repo → Settings → Webhooks → Payload URL `https://<ngrok-id>.ngrok-free.app/github-webhook/`,
content type `application/json`. In Jenkins job → Configure → Build Triggers → tick **GitHub hook trigger for GITScm polling**.

---
## Project structure
```
app.py                Streamlit dashboard (Predict • Batch • Model & metrics • Monitoring)
params.yaml           hyper-parameters & thresholds        dvc.yaml   pipeline stages
Jenkinsfile           Windows CI/CD + schedule             Dockerfile, docker-compose.yml
src/                  generate_data • preprocess • pipeline • train • evaluate • monitor • predictor • api
tests/                pytest suite                         scripts/   .bat helpers + smoke_test.py
```
Convenience scripts (same commands as above): `scripts\setup.bat`, `scripts\run_pipeline.bat`,
`scripts\start_api.bat`, `scripts\start_streamlit.bat`, `scripts\start_mlflow.bat`,
`scripts\push_to_github.bat <repo-url>`, `scripts\check_prereqs.bat`.

## Viva cheat-sheet
* **DVC** versions data/models/stages so any result is reproducible from a Git commit. **MLflow** logs params, metrics,
  artifacts and registers the best of 3 models. **Quality gate** (`evaluate.py`: F1 ≥ 0.75, ROC-AUC ≥ 0.80) stops bad models
  from being deployed. **Drift** = PSI of live inputs vs training data; PSI > 0.2 ⇒ retrain (nightly Jenkins job does it).
* Dataset is synthetic + seeded (reproducible). Swap `src/generate_data.py` for the UCI Student Performance CSV if needed.
