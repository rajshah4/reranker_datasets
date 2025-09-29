#!/usr/bin/env python3
import os
import sys
import subprocess
import shutil
import hashlib
from datetime import date
from pathlib import Path
from typing import List, Tuple

from huggingface_hub import HfApi, hf_hub_download
from dotenv import load_dotenv

# -----------------------
# Config / Inputs
# -----------------------
load_dotenv()

GH_OWNER = "rajshah4"             # e.g., "your-org"
GH_REPO  = "reranker_datasets"    # just the repo name, not owner/repo
RELEASE_TAG="v1.0"
HF_TOKEN = os.getenv("HF_TOKEN")
# e.g., "your-repo"
          # needed for private repos

# Add your datasets here (HF "org/name")
DATASETS = [
    "ContextualAI/touche2020",
    "ContextualAI/msmarco",
    "ContextualAI/treccovid",
    "ContextualAI/nq",
    "ContextualAI/hotpotqa",
    "ContextualAI/fiqa2018",
]

# Where to place small files in the repo
DATASETS_DIR = Path("datasets")    # repo-relative path
CHECKSUMS_DIR = Path("checksums")  # repo-relative path
SCRIPTS_DIR = Path("scripts")      # repo-relative path
TMP_DIR = Path(".tmp_mirror")      # temp download cache

SMALL_FILE_LIMIT = 50 * 1024 * 1024  # 50 MB

# -----------------------
# Helpers
# -----------------------
def run(cmd: List[str], check=True, cwd=None):
    print(f"→ Running: {' '.join(cmd)}")
    return subprocess.run(cmd, check=check, cwd=cwd)

def sha256sum(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def ensure_dirs():
    for d in [DATASETS_DIR, CHECKSUMS_DIR, SCRIPTS_DIR, TMP_DIR]:
        d.mkdir(parents=True, exist_ok=True)

def gh_release_exists(owner: str, repo: str, tag: str) -> bool:
    # returns True if release exists
    res = subprocess.run(
        ["gh", "release", "view", tag, "-R", f"{owner}/{repo}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return res.returncode == 0

def create_or_get_release(owner: str, repo: str, tag: str):
    if not gh_release_exists(owner, repo, tag):
        run(["gh", "release", "create", tag, "-R", f"{owner}/{repo}", "-t", tag, "-n", f"Auto-mirrored on {date.today().isoformat()}"])
    else:
        print(f"✓ Release {tag} already exists")

def upload_assets(owner: str, repo: str, tag: str, files: List[Path]):
    if not files:
        return
    args = ["gh", "release", "upload", tag] + [str(f) for f in files] + ["-R", f"{owner}/{repo}"]
    run(args)

def git_add_commit_push(msg: str):
    run(["git", "add", "-A"])
    # Commit can fail if nothing to commit; ignore in that case
    res = subprocess.run(["git", "commit", "-m", msg])
    if res.returncode != 0:
        print("No changes to commit.")
    else:
        run(["git", "push", "origin", "HEAD"])

def normalize_repo_id(repo_id: str) -> str:
    # "org/name" -> ("org","name")
    if "/" not in repo_id:
        raise ValueError("Dataset repo_id must be in the form 'org/name'")
    return repo_id

# -----------------------
# Core
# -----------------------
def mirror_dataset(repo_id: str) -> Tuple[List[Path], List[Tuple[Path, str]]]:
    """
    Downloads all files from an HF dataset repo and partitions into:
    - small_files: to be committed in-repo under datasets/<name>/
    - big_files: to be uploaded to release assets (list of (path, relpath))
    Returns (small_files_paths, big_files_paths_with_relpath)
    """
    api = HfApi(token=HF_TOKEN)
    repo_id = normalize_repo_id(repo_id)
    org, name = repo_id.split("/", 1)

    print(f"\n=== Mirroring {repo_id} ===")
    info = api.dataset_info(repo_id=repo_id, token=HF_TOKEN)

    dataset_root = DATASETS_DIR / name
    dataset_root.mkdir(parents=True, exist_ok=True)

    small_files = []
    big_files = []  # list of (local_path, relative_path_for_checksums)

    # info.siblings -> files in repo (rfilename, size)
    for sib in info.siblings:
        rpath = sib.rfilename
        size = getattr(sib, "size", None)

        # Skip ".gitattributes" and HF-specific symlinks if any
        if rpath.endswith(".gitattributes"):
            continue

        # Create local temp path
        local_tmp = TMP_DIR / name / rpath
        local_tmp.parent.mkdir(parents=True, exist_ok=True)

        # Download file
        print(f"Downloading: {rpath} ({size} bytes)")
        downloaded_path = hf_hub_download(
            repo_id=repo_id,
            filename=rpath,
            repo_type="dataset",
            local_dir=str(local_tmp.parent),
            local_dir_use_symlinks=False,
            token=HF_TOKEN,
        )

        # The downloaded file might be in a different location than expected
        # Check if the file exists at the expected location, otherwise use the returned path
        if local_tmp.exists():
            actual_path = local_tmp
        else:
            actual_path = Path(downloaded_path)
            print(f"File downloaded to: {actual_path}")
            
        # Verify the file actually exists
        if not actual_path.exists():
            print(f"ERROR: Downloaded file does not exist at {actual_path}")
            print(f"Expected location: {local_tmp}")
            print(f"Returned path: {downloaded_path}")
            continue

        # Partition by size (fallback: if size is None, check stat)
        fsize = size if size is not None else actual_path.stat().st_size
        if fsize <= SMALL_FILE_LIMIT:
            # copy into repo under datasets/<name>/<rpath>
            dest = dataset_root / rpath
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(actual_path, dest)
            small_files.append(dest)
        else:
            # mark for release upload
            rel = f"{name}/{rpath}"  # logical relative within datasets folder
            big_files.append((actual_path, rel))

    return small_files, big_files

def write_checksums_and_scripts(all_small: List[Path], all_big: List[Tuple[Path, str]]):
    # checksums/sha256.txt contains both small (as stored in repo path) and big (as release rel path)
    # For big files, we keep the "logical" datasets/<rel> path in the manifest comment,
    # but users will actually download via release URL.
    cfile = CHECKSUMS_DIR / "sha256.txt"
    lines = []
    print("\nComputing checksums...")
    for p in sorted(all_small):
        h = sha256sum(p)
        # store path relative to repo root
        rel = p.as_posix()
        lines.append(f"{h}  {rel}")

    for p, rel in sorted(all_big, key=lambda x: x[1]):
        h = sha256sum(p)
        lines.append(f"{h}  datasets/{rel}")

    cfile.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"✓ Wrote {cfile}")

    # download.sh: pulls big files from release assets, leaves small files to git clone
    scripts = []
    gh_release_base = f"https://github.com/{GH_OWNER}/{GH_REPO}/releases/download/{RELEASE_TAG}"

    dl_lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        f'BASE="{gh_release_base}"',
        'mkdir -p datasets',
    ]
    for _p, rel in sorted(all_big, key=lambda x: x[1]):
        out_path = f"datasets/{rel}"
        dl_lines.append(f'mkdir -p "$(dirname \\"{out_path}\\")"')
        dl_lines.append(f'curl -L -o "{out_path}" "$BASE/{Path(rel).name}"  # Adjust if you changed asset names')

    (SCRIPTS_DIR / "download.sh").write_text("\n".join(dl_lines) + "\n", encoding="utf-8")
    run(["chmod", "+x", str(SCRIPTS_DIR / "download.sh")])
    print(f"✓ Wrote {SCRIPTS_DIR/'download.sh'}")

    # verify.sh
    ver_lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        'if command -v sha256sum >/dev/null 2>&1; then',
        f'  (sha256sum -c "{CHECKSUMS_DIR}/sha256.txt")',
        "else",
        f'  (shasum -a 256 -c "{CHECKSUMS_DIR}/sha256.txt")',
        "fi",
    ]
    (SCRIPTS_DIR / "verify.sh").write_text("\n".join(ver_lines) + "\n", encoding="utf-8")
    run(["chmod", "+x", str(SCRIPTS_DIR / "verify.sh")])
    print(f"✓ Wrote {SCRIPTS_DIR/'verify.sh'}")

def main():
    if not GH_OWNER or not GH_REPO:
        print("ERROR: Set GH_OWNER and GH_REPO in your environment.")
        sys.exit(1)
    if not DATASETS:
        print("ERROR: Populate the DATASETS list in this script.")
        sys.exit(1)

    ensure_dirs()

    all_small_files: List[Path] = []
    all_big_files: List[Tuple[Path, str]] = []

    # 1) Download + partition each dataset
    for repo_id in DATASETS:
        small, big = mirror_dataset(repo_id)
        all_small_files.extend(small)
        all_big_files.extend(big)

    # Check if GitHub CLI is available and authenticated
    try:
        # Test if gh is available and authenticated
        subprocess.run(["gh", "auth", "status"], check=True, capture_output=True)
        github_available = True
        print("✓ GitHub CLI is available and authenticated")
    except (subprocess.CalledProcessError, FileNotFoundError):
        github_available = False
        print("⚠️  GitHub CLI not available or not authenticated. Skipping GitHub operations.")
        print("   To enable GitHub operations, run: gh auth login")

    if github_available:
        # 2) Create (or reuse) release
        create_or_get_release(GH_OWNER, GH_REPO, RELEASE_TAG)

        # 3) Upload big assets to release (flatten asset names or keep paths)
        # We'll upload assets with just the basename to keep URLs short.
        # If you need path context, rename here (e.g., prefix with dataset name).
        upload_list = []
        for p, rel in all_big_files:
            # Upload with basename; if collisions possible, prefix with dataset name
            target = p
            # Optionally rename to include dataset: f"{rel.replace('/','__')}"
            # For simplicity, keep basename:
            upload_list.append(target)

        if upload_list:
            upload_assets(GH_OWNER, GH_REPO, RELEASE_TAG, upload_list)

        # 5) Commit & push small files + manifests
        git_add_commit_push(f"Mirror HF datasets → small files in repo; big files → release {RELEASE_TAG}")

        print("\nDone ✅")
        print("USAGE for consumers:")
        print("1) git clone https://github.com/{}/{}".format(GH_OWNER, GH_REPO))
        print("2) ./scripts/download.sh   # fetches >50 MB assets from Release")
        print("3) ./scripts/verify.sh     # verifies all files")
        print("\nRelease URL: https://github.com/{}/{}/releases/tag/{}".format(GH_OWNER, GH_REPO, RELEASE_TAG))
    else:
        print("\nDone ✅ (GitHub operations skipped)")
        print("Downloaded files are available in:")
        print(f"- Small files: {DATASETS_DIR}")
        print(f"- Big files: {TMP_DIR}")
        print("\nTo complete GitHub operations:")
        print("1) Run: gh auth login")
        print("2) Re-run this script")

    # 4) Checksums + scripts (always generate these)
    write_checksums_and_scripts(all_small_files, all_big_files)

if __name__ == "__main__":
    main()
