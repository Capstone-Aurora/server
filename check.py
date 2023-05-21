import os


def dependency_check(fileName):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    data_path = dir_path + "/data"
    my_file_path = os.path.join(data_path, fileName)

    dependency_list = []
    myfile = open(my_file_path, "r")
    code = myfile.read()

    if "import" in code:
        code = code.split("import")
        for i in range(1, len(code)):
            dependency_list.append(code[i].split()[0])
    if "from" in code:
        code = code.split("from")
        for i in range(1, len(code)):
            dependency_list.append(code[i].split()[0])

    myfile.close()

    return dependency_list
