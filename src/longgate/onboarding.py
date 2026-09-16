AI_SETUP_PROMPT = """You are configuring Long Gate in MODEL SETUP MODE.

Goal:
Install and verify a local model so Long Gate can later process sensitive data
without network access.

Security rules you MUST follow:
1. Do not open, inspect, summarize, upload, or search for any private/user dataset.
2. Do not ask me to paste sensitive data into this chat.
3. Setup mode may use the Internet only for software/model installation.
4. Do not configure a remote LLM endpoint for private processing.
5. Do not configure Ollama/HTTP/cloud APIs as Long Gate's private semantic engine.
6. The private processing phase must use a local GGUF file from Long Gate's Model Vault.
7. Do not weaken Long Gate's fail-closed policies or add a force-release option.

Proceed autonomously unless administrator privileges or destructive actions are required.

Tasks:
A. Check OS, Python version, available disk space, and system RAM.
B. Obtain/update the Long Gate repository from:
   https://github.com/CochraneK/long-gate
C. Create a Python virtual environment.
D. Install:
   pip install -e '.[models,local-llm,documents,stats]'
E. Run:
   longgate doctor
F. Run the one-command setup:
   longgate model setup
   This must automatically recommend, download, SHA-256 verify, and set a default model.
   If automatic RAM detection fails, rerun:
   longgate model setup --ram-gb <detected RAM>
G. Run:
   longgate model verify auto
H. Run:
   longgate model list
J. Do NOT test with a real sensitive document. If a smoke test is useful, create a
   tiny synthetic text file containing invented information only.
K. At the end, report:
   - Python version
   - detected RAM
   - default model alias
   - model file path
   - SHA-256 verification result
   - whether llama_cpp is available
   - the exact private-processing command I can run later

Explain that model installation is a network-enabled setup step, while the later
private-processing worker should have network disabled.

If something fails, diagnose and repair it while preserving every security rule above.
"""
