# Run the current demo in IBM Bob

This folder is the active project. Docker is the runtime; Bob is the IDE.

1. Choose Terminal > Run Task > HR: Run existing demo (no rebuild).
2. Choose Terminal > Run Task > HR: Service status.
3. Open http://127.0.0.1:8000/docs on this laptop.
4. Choose Terminal > Run Task > HR: Regression tests for the offline contract suite.

Selected extraction: Antigravity with explicit Gemini 3.7 Flash, using the private
Google key. CUDA embeddings are local. Do not select the installer task again.
Do not paste .env, expanded Docker configuration or credentials into Bob chat.

The equivalent command in Bob's integrated terminal is:

```powershell
docker compose up -d --no-build --wait --wait-timeout 180
```

Bob may ask for workspace trust or permission to run terminal commands. Review the
project path and the commands above. Such prompts require your interaction.
