import os
import ast


def dependency_check(fileName):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    data_path = dir_path + "/data"
    my_file_path = os.path.join(data_path, fileName)

    dependency_list = []

    myfile = open(my_file_path, "r")
    tree = ast.parse(myfile.read())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                dependency_list.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            dependency_list.append(node.module)

    myfile.close()

    return dependency_list
