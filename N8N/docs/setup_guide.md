# Setup Guide

## Prerequisites
- Windows 10/11
- Anaconda/Miniconda with Python 3.8+
- Docker Desktop
- Git

## Step 1: Create Project Structure
1. Run the following batch file to create folders:
   ```cmd
   D:\create_folders.bat
   ```

## Step 2: Initialize Git
1. Open Command Prompt and navigate to the project directory:
   ```cmd
   cd D:\Hydride_Machine_learning_project\N8N
   ```
2. Initialize Git:
   ```cmd
   git init
   ```

## Step 3: Install Anaconda/Miniconda
1. Check Conda version:
   ```cmd
   conda --version
   ```
2. If not installed, download from [anaconda.com](https://www.anaconda.com/) or [conda.io](https://docs.conda.io/en/latest/miniconda.html).

## Step 4: Activate Conda Environment
1. Activate the `Project` environment:
   ```cmd
   conda activate Project
   ```

## Step 5: Install Docker Desktop
1. Download and install from [docker.com](https://www.docker.com/products/docker-desktop/).
2. Verify installation:
   ```cmd
   docker --version
   ```

## Step 6: Run n8n
1. Create a Docker volume and run n8n:
   ```cmd
   docker volume create n8n_data
   docker run -it --rm --name n8n -p 5678:5678 -v n8n_data:/home/node/.n8n docker.n8n.io/n8nio/n8n
   ```
2. Access n8n at `http://localhost:5678`.

## Step 7: Install Python Dependencies
1. Activate the Conda environment:
   ```cmd
   conda activate Project
   ```
2. Install Conda packages:
   ```cmd
   conda install -c conda-forge rdkit=2023.9.6 numpy=1.26.4 scikit-learn=1.5.1 joblib=1.4.2 pytest=8.3.3
   ```
3. Install pip packages:
   ```cmd
   pip install fastapi==0.115.0 uvicorn==0.30.6
   ```

## Notes for Iran
- If package installation fails due to sanctions, download Conda package files (e.g., `rdkit-2023.9.6.tar.bz2`) and install offline:
  ```cmd
  conda install D:\path\to\rdkit-2023.9.6.tar.bz2
  ```
- Use a VPN if Docker image download fails.