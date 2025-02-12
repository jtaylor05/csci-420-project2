with open("loadserver.yaml", "w") as yamlOut:
    with open("loadserver.yaml.src", "r") as baseIn:
        yamlOut.writelines(baseIn.readlines())
    with open("loadserver.py", "r") as piIn:
        for line in piIn.readlines():
            yamlOut.write(f"        {line}")
