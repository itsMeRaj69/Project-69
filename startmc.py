import os
import subprocess

# Set your RAM limit (e.g. 2G, 512M, etc.)
RAM = "2G"

# Server setup
server_dir = "/workspaces/Haggupur/minecraft_server/"
jar_file = "paper.jar"
jar_path = os.path.join(server_dir, jar_file)
eula_path = os.path.join(server_dir, "eula.txt")

# Accept EULA
if not os.path.exists(eula_path) or "eula=true" not in open(eula_path).read():
    with open(eula_path, "w") as f:
        f.write("eula=true\n")
    print("EULA accepted.")

# Start the server
print(f"Starting server with RAM={RAM}")
subprocess.run([
    "java",
    f"-Xms{RAM}",
    f"-Xmx{RAM}",
    "-jar",
    jar_path,
    "nogui"
], cwd=server_dir)