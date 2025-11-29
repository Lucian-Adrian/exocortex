# Deploy script to create project structure

param(
    [switch]$Force
)

Write-Host "Starting project structure deployment..." -ForegroundColor Green

# Function to create directory with check
function New-Directory {
    param([string]$Path)
    if (Test-Path $Path) {
        if (-not $Force) {
            $response = Read-Host "Directory '$Path' already exists. Overwrite? (y/N)"
            if ($response -ne 'y' -and $response -ne 'Y') {
                Write-Host "Skipping '$Path'" -ForegroundColor Yellow
                return
            }
        }
        Remove-Item -Recurse -Force $Path
    }
    New-Item -ItemType Directory -Path $Path | Out-Null
    Write-Host "Created directory: $Path" -ForegroundColor Cyan
}

# Function to create file with check
function New-File {
    param([string]$Path, [string]$Content)
    if (Test-Path $Path) {
        if (-not $Force) {
            $response = Read-Host "File '$Path' already exists. Overwrite? (y/N)"
            if ($response -ne 'y' -and $response -ne 'Y') {
                Write-Host "Skipping '$Path'" -ForegroundColor Yellow
                return
            }
        }
    }
    $Content | Out-File -FilePath $Path -Encoding UTF8
    Write-Host "Created file: $Path" -ForegroundColor Cyan
}

try {
    # Create directories
    New-Directory -Path .github
    New-Directory -Path config
    New-Directory -Path docs
    New-Directory -Path docs\backend
    New-Directory -Path docs\db
    New-Directory -Path docs\frontend
    New-Directory -Path docs\info
    New-Directory -Path docs\tests

    # Create files with content
    $copilotContent = @"
# Copilot Instructions

Add your custom instructions for GitHub Copilot here.

## Example Instructions
- Use consistent naming conventions
- Write clear, concise comments
- Follow the project's coding standards
"@

    New-File -Path .github\copilot-instructions.md -Content $copilotContent

    $fileStructureContent = @"
# Project File Structure

## Directory Tree

```
project-root/
├── .github/
│   └── copilot-instructions.md
├── config/
│   ├── .editorconfig
│   ├── deploy.ps1
│   ├── deploy.sh
│   ├── Dockerfile
│   └── docker-compose.yml
├── docs/
│   ├── backend/
│   ├── db/
│   ├── file-structure.md
│   ├── frontend/
│   ├── info/
│   └── tests/
├── .gitignore
├── changelog.md
├── contributing.md
└── readme.md
```
"@

    New-File -Path docs\file-structure.md -Content $fileStructureContent

    $changelogContent = @"
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project structure
- Basic documentation

### Changed

### Deprecated

### Removed

### Fixed

### Security
"@

    New-File -Path changelog.md -Content $changelogContent

    $contributingContent = @"
# Contributing

Thank you for your interest in contributing! Please follow these guidelines:

## How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Code Style

- Follow the existing code style
- Write clear, concise commit messages
- Add tests for new features
- Update documentation as needed

## Reporting Issues

Please use the GitHub issue tracker to report bugs or request features.
"@

    New-File -Path contributing.md -Content $contributingContent

    $readmeContent = @"
# My Project

A brief description of your project.

## Features

- Feature 1
- Feature 2
- Feature 3

## Installation

```bash
# Installation instructions
```

## Usage

```bash
# Usage examples
```

## Contributing

See [CONTRIBUTING.md](contributing.md) for details.
"@

    New-File -Path readme.md -Content $readmeContent

    # Create additional files
    $editorconfigContent = @"
root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true

[*.{js,py}]
indent_style = space
indent_size = 4

[*.{html,css}]
indent_style = space
indent_size = 2
"@

    New-File -Path config\.editorconfig -Content $editorconfigContent

    # Create Docker files
    $dockerfileContent = @"
# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 80 available to the world outside this container
EXPOSE 80

# Define environment variable
ENV NAME World

# Run app.py when the container launches
CMD ["python", "app.py"]
"@

    New-File -Path config\Dockerfile -Content $dockerfileContent

    $dockerComposeContent = @"
version: '3.8'

services:
  app:
    build: .
    ports:
      - "4000:80"
    volumes:
      - .:/app
"@

    New-File -Path config\docker-compose.yml -Content $dockerComposeContent

    # Create .gitignore
    $gitignoreContent = @"
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
#  Usually these files are written by a python script from a template
#  before PyInstaller builds the exe, so as to inject date/other infos into it.
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
.hypothesis/
.pytest_cache/

# Translations
*.mo
*.pot

# Django stuff:
*.log
local_settings.py
db.sqlite3

# Flask stuff:
instance/
.webassets-cache

# Scrapy stuff:
.scrapy

# Sphinx documentation
docs/_build/

# PyBuilder
target/

# Jupyter Notebook
.ipynb_checkpoints

# IPython
profile_default/
ipython_config.py

# pyenv
.python-version

# celery beat schedule file
celerybeat-schedule

# SageMath parsed files
*.sage.py

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Spyder project settings
.spyderproject
.spyproject

# Rope project settings
.ropeproject

# mkdocs documentation
/site

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Logs
logs
*.log

# Runtime data
pids
*.pid
*.seed
*.pid.lock

# Directory for instrumented libs generated by jscoverage/JSCover
lib-cov

# Coverage directory used by tools like istanbul
coverage/

# nyc test coverage
.nyc_output

# Grunt intermediate storage (http://gruntjs.com/creating-plugins#storing-task-files)
.grunt

# Bower dependency directory (https://bower.io/)
bower_components

# node-waf configuration
.lock-waf

# Compiled binary addons (https://nodejs.org/api/addons.html)
build/Release

# Dependency directories
jspm_packages/

# TypeScript v1 declaration files
typings/

# Optional npm cache directory
.npm

# Optional eslint cache
.eslintcache

# Microbundle cache
.rscache

# Optional REPL history
.node_repl_history

# Output of 'npm pack'
*.tgz

# Yarn Integrity file
.yarn-integrity

# dotenv environment variables file
.env

# parcel-bundler cache (https://parceljs.org/)
.cache
.parcel-cache

# next.js build output
.next

# nuxt.js build output
.nuxt

# vuepress build output
.vuepress/dist

# Serverless directories
.serverless

# FuseBox cache
.fusebox/

# DynamoDB Local files
.dynamodb/

# TernJS port file
.tern-port

# Stores VSCode versions used for testing VSCode extensions
.vscode-test

# Temporary folders
tmp/
temp/

# Database
*.db
*.sqlite
*.sqlite3

# Docker
.dockerignore

# Git
.git
.gitignore

# Project specific
docs/
"@

    New-File -Path .gitignore -Content $gitignoreContent

    Write-Host "Project structure deployed successfully!" -ForegroundColor Green
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Update the README.md with your project details"
    Write-Host "2. Customize the .github/copilot-instructions.md"
    Write-Host "3. Initialize git: git init && git add . && git commit -m 'Initial commit'"

    # Clean up the deploy script
    Remove-Item -Path $PSCommandPath -Force
} catch {
    Write-Host "Error during deployment: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}