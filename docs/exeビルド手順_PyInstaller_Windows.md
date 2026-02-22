# Windows向け exe ビルド手順（PyInstaller）

このドキュメントは、本プロジェクト（`main.py`）を **Windows向けの実行ファイル（`.exe`）** にビルドし、成果物を **`build/` フォルダ配下**に出力する手順をまとめたものです。

本リポジトリには、PyInstaller 用の設定ファイル `main.spec` が同梱されています。
この `.spec` は `assets/` と `scripts/` を同梱する設定になっており、さらに出力先を `build/` に寄せています。

---

## 1. 事前条件

- Windows
- Python 3.10 以上
- （推奨）venv

---

## 2. 依存の準備（venv 推奨）

プロジェクトルート（`main.py` がある場所）で実行します。

### 2.1 venv 作成

```bash
python -m venv venv
```

### 2.2 venv 有効化（PowerShell）

```powershell
venv\Scripts\Activate.ps1
```

### 2.3 依存のインストール

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 2.4 PyInstaller のインストール

PyInstaller が未導入の場合のみ実行します。

```bash
pip install pyinstaller
```

---

## 3. exe をビルドして build/ に格納

このプロジェクトでは `main.spec` を使うのが最短です。

ビルド用スクリプトも同梱されています（フォルダ作成を確実に行うため、こちら推奨）。

### 3.1 （推奨）PowerShell スクリプトでビルド

```powershell
./build.ps1
```

### 3.2 （推奨）Python スクリプトでビルド

```bash
python scripts/build_exe.py
```

### 3.3 直接 PyInstaller を叩いてビルド

```bash
pyinstaller main.spec
```

成功すると以下が生成されます。

- `build/main.exe`（実行ファイル本体）
- `build/assets/`（同梱データ）
- `build/scripts/`（同梱データ）
- `build/temp/`（PyInstaller の作業ディレクトリ）

`main.spec` 内で `distpath` と `workpath` を `build/` 配下に指定しているため、原則ここにまとまります。

---

## 4. 実行確認

ビルド後は、`build/main.exe` をダブルクリックで起動します。

起動しない場合は、まず PowerShell から実行してエラーを確認してください。

```powershell
.\build\main.exe
```

---

## 5. よくあるトラブル

### 5.0 `base_library.zip` が作れない（`FileNotFoundError`）

例：

```
FileNotFoundError: ... build\\temp\\base_library.zip
```

- `build/temp` フォルダが存在しない状態で PyInstaller が書き込もうとしている可能性があります。
- 上の **`build.ps1`** または **`python scripts/build_exe.py`** を使うと解決します。
- 直接ビルドする場合は、事前に `build/` と `build/temp/` を作成してください。

### 5.1 ウイルス対策ソフトが exe を隔離する

PyInstaller 生成物は環境によって誤検知されることがあります。

- 隔離された場合は、例外設定（除外）を入れて再ビルドしてください。

### 5.2 画像/音が読み込めない（assets が見つからない）

本プロジェクトは `main.spec` にて `assets/` を同梱する設定です。

- `main.spec` の `datas=[("assets", "assets"), ("scripts", "scripts")] ...` を変更していないか確認してください。

### 5.3 ビルドは成功するが起動時に落ちる

まずコンソールから起動してログを確認してください。

```powershell
.\build\main.exe
```

---

## 6. クリーンビルドしたい場合

`build/temp/` は作業ディレクトリです。
不具合調査のために作り直したい場合は、以下を削除してから再ビルドします。

- `build/temp/`

その後、もう一度

```bash
pyinstaller main.spec
```

を実行してください。
