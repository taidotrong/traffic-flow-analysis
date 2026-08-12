# Chuẩn bị và push lên GitHub

Thư mục local do Codex chuẩn bị đã được `git init -b main` và toàn bộ file hợp lệ đã được stage. Chưa có commit vì máy chưa cấu hình `user.name`/`user.email`, và chưa có remote vì chưa được cung cấp URL repository GitHub.

## Từ thư mục local hiện tại

```bash
cd /Users/taidotrong/.codex/.chatgpt-projects/g-p-6a5c726aae348191afd47c2c638955c0/traffic-flow-analysis

git config user.name "TEN_CUA_BAN"
git config user.email "EMAIL_GITHUB_CUA_BAN"
git commit -m "Initial traffic flow analysis baseline"
```

Tạo một repository trống trên GitHub (không khởi tạo thêm README/.gitignore), rồi thêm remote và push:

```bash
git remote add origin git@github.com:USERNAME/REPOSITORY.git
git push -u origin main
```

Nếu dùng HTTPS:

```bash
git remote add origin https://github.com/USERNAME/REPOSITORY.git
git push -u origin main
```

## Dùng GitHub CLI

Sau khi `gh auth login`, có thể tạo repo và push trong một lệnh. Chọn đúng `--private` hoặc `--public`:

```bash
gh repo create REPOSITORY --source=. --remote=origin --private --push
```

## Nếu bắt đầu từ ZIP

```bash
unzip traffic-flow-analysis-github-ready.zip
cd traffic-flow-analysis
git init -b main
git add .
git commit -m "Initial traffic flow analysis baseline"
git remote add origin git@github.com:USERNAME/REPOSITORY.git
git push -u origin main
```

## Kiểm tra trước khi push

```bash
git diff --cached --check
git status --short
git remote -v
```

Không dùng `git add -f` cho dataset, checkpoint hoặc archive lớn. Các mục `data/`, `runs/`, `outputs/`, `*.pt` và `*.zip` đã được `.gitignore` loại trừ. Nếu muốn phát hành checkpoint, ưu tiên GitHub Releases hoặc Git LFS.
