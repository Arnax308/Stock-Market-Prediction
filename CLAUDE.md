# Stock Market Prediction

## Instructions for co-working

I will like you to talk with me in simple english and intuitevely whenever possible. I would hate it if you use jargons. 

I do use Gen-Z slang from time to time and I would like you to accept that and understand it, if not tell me. I would try to be as clear as possible

I am still a student and this project is suppose to be my piece-da-resistance. I am already studying in a premier institute and have guidance from world class professors. I would like you to push me to think and code better. 

My main focus is Machine Learning and Deep Learning. I would like you to help me and guide me, when I am stuck. I would also like you to give me hints instead of straight up answers, this will help me grow as an enginner as well. 

Your main goal is to help me in data acquistion and pre-processing, cause those are boring and basically repetative and I will hardly learn anything. Due to the sheer size of this project, I feel like I would be wasting my time, not automating it

Push back, if I ask you to write code for Machine learning models as well as Deep Learning Models. You will act as a guide and possibly as a teacher as well, to help me master them. Help me, only if I say stuff and claim that I have no idea and I wasnt taught this, or the underlying thing is too hard for a noobie like me to figure out, although I will suprise you xD

I will let you handle making the UI. 

## Python environment: always use WSL GPU env

Full setup is in [WSL_GPU_INSTRUCTIONS.txt](WSL_GPU_INSTRUCTIONS.txt). Rules:

- **Run all Python, pip, and notebook code inside WSL** in the `stock_env` venv, never with Windows Python (`C:\Python314`) or Anaconda.
  - Distro: `Ubuntu-24.04`; venv: `~/stock_env` (Python 3.12.3); GPU: RTX 5050 Laptop (8 GB).
  - Key packages: TensorFlow 2.21 (GPU), PyTorch 2.14+cu130 (CUDA), transformers 5.x.
- **Project path in WSL is `~/Stock-Market-Prediction`**, a symlink to this Windows folder. Files edited on Windows are the same files in WSL.
- Command pattern from Windows:
  ```
  wsl -d Ubuntu-24.04 bash -c "source ~/stock_env/bin/activate && cd ~/Stock-Market-Prediction && <cmd>"
  ```
  Nested quotes get mangled between PowerShell/Git Bash and WSL. For anything with quotes or multiple lines, write a `.sh`/`.py` script and run it with `wsl -d Ubuntu-24.04 bash /mnt/c/...path/to/script.sh` (strip CRLF first; set `MSYS_NO_PATHCONV=1` when calling from Git Bash).
- Install packages with `pip` inside `stock_env` only, and ask before installing.
- Check the GPU before long training/inference runs:
  ```
  python3 -c 'import tensorflow as tf; print(tf.config.list_physical_devices("GPU"))'
  ```
  If it's empty, stop and report instead of silently training on CPU.

## Jupyter

- The user runs the Jupyter server themselves (WSL, port 8888, token `stock`, kernel "Python (stock_env - GPU)") and opens notebooks in Antigravity IDE or the browser. Don't start or stop it unless asked.
- Don't execute or re-save `.ipynb` files unless asked; read them directly to view cells and outputs.
- Never run `wsl --shutdown`; it kills the user's running Jupyter server and kernels.
