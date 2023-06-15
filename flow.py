from bigcode_astgen import ast_generator
from collections import deque
import os
import ast
import sys
import re

name_set = set()
var_dic = {}
event_graph = []


def get_flow(fileNum):
    # filename=sys.argv[1]
    # source_code=open(filename,"r").read().split('\n')
    # src_rule=open(sys.argv[2],"r").read().split('\n')
    # san_rule=open(sys.argv[3],"r").read().split('\n')
    # snk_rule=open(sys.argv[4],"r").read().split('\n')
    example_list = ["temp.txt", "temp.txt", "temp.txt", "temp.txt"]

    dir_path = (
        os.path.dirname(os.path.realpath(__file__))
        + "/example"
        + "/ex"
        + fileNum.__str__()
        + "/"
    )

    filename = dir_path + example_list[fileNum].__str__()
    source_code = open(filename, "r").read().split("\n")
    src_rule = open(dir_path + "src.txt", "r").read().split("\n")
    san_rule = open(dir_path + "san.txt", "r").read().split("\n")
    snk_rule = open(dir_path + "snk.txt", "r").read().split("\n")

    parsed = ast_generator.parse_file(filename)

    def get_inst(x):
        ans = []
        for child in parsed[x]["children"]:
            if parsed[child]["type"] == "Try":
                body = parsed[child]["children"][0]
                assert parsed[body]["type"] == "body"
                ans += get_inst(body)
                # """
                handlers = parsed[child]["children"][1]
                assert parsed[handlers]["type"] == "handlers"
                for handle in parsed[handlers]["children"]:
                    body = parsed[handle]["children"][-1]
                    assert parsed[body]["type"] == "body"
                    ans += get_inst(body)
                # """

            elif "If" in parsed[child]["type"]:
                ans.append(parsed[child]["children"][0])
                body = parsed[child]["children"][1]
                assert parsed[body]["type"] == "body"
                ans += get_inst(body)
            elif "Import" in parsed[child]["type"]:
                continue
            elif "Def" in parsed[child]["type"]:
                continue
            else:
                ans.append(child)
        return ans

    def get_import(x):
        ans = []
        for child in parsed[x]["children"]:
            if parsed[child]["type"] == "Try":
                body = parsed[child]["children"][0]
                assert parsed[body]["type"] == "body"
                ans += get_import(body)
                # """
                handlers = parsed[child]["children"][1]
                assert parsed[handlers]["type"] == "handlers"
                for handle in parsed[handlers]["children"]:
                    body = parsed[handle]["children"][-1]
                    assert parsed[body]["type"] == "body"
                    ans += get_import(body)
                # """
            elif "Import" in parsed[child]["type"]:
                ans.append(child)
        return ans

    def get_def(x):
        ans = []
        for child in parsed[x]["children"]:
            if "Def" in parsed[child]["type"]:
                ans.append(child)
        return ans

    def get_name(where, x):
        name = parsed[x]["value"]
        result = where.split("::")[:-1]
        prefixes = [""] + ["::".join(result[:i]) + "::" for i in range(1, len(result))]
        for _ in prefixes[::-1]:
            if _ + name in name_set:
                return _ + name
        return where + name

    def get_attrname(where, x):
        base = parsed[x]["children"][0]
        attr = parsed[x]["children"][1]
        name, arg = get_rep(where, base)
        assert parsed[attr]["type"] == "attr"
        return name + "." + parsed[attr]["value"], arg

    def get_susname(where, x):
        base = parsed[x]["children"][0]
        idx = parsed[x]["children"][1]
        name, arg = get_rep(where, base)
        assert parsed[idx]["type"] == "Index"
        idx = parsed[idx]["children"][0]
        name += "[" + get_rep(where, idx)[0] + "]"
        if parsed[idx]["type"] != "Constant":
            arg.append(get_rep(where, idx))
        return name, arg

    def get_rep(where, x):
        if parsed[x]["type"] in [
            "BoolOpOr",
            "BinOpMod",
            "BinOpAdd",
            "ListLoad",
            "TupleStore",
            "TupleLoad",
            "JoinedStr",
            "FormattedValue",
        ]:
            args = []
            for child in parsed[x]["children"]:
                temp = get_rep(where, child)
                if isinstance(temp, list):
                    args += temp
                else:
                    args.append(get_rep(where, child))
            return args
        if parsed[x]["type"] in ["keyword", "StarredLoad"]:
            return get_rep(where, parsed[x]["children"][0])
        if parsed[x]["type"] == "Call":
            base = parsed[x]["children"][0]
            name, args = get_rep(where, base)
            if "." in name:
                self = name.rsplit(".", 1)[0]
                if "::" in self or "[" in self:
                    args = [(self, args)]
            for arg in parsed[x]["children"][1:]:
                temp = get_rep(where, arg)
                if isinstance(temp, list):
                    args += temp
                else:
                    args.append(temp)
            return name + "()", args
        if "Name" in parsed[x]["type"]:
            return get_name(where, x), []
        if "Attribute" in parsed[x]["type"]:
            return get_attrname(where, x)
        if "Subscript" in parsed[x]["type"]:
            return get_susname(where, x)
        if parsed[x]["type"] == "Constant":
            try:
                value = parsed[x]["value"]
            except KeyError:
                value = ""
            try:
                int(value)
                return value, []
            except ValueError:
                pass
            try:
                float(value)
                return value, []
            except ValueError:
                pass
            if value.lower() == "true" or value.lower() == "false":
                return value.lower() == "true", []
            return "'" + value + "'", []

    def represent(where, x):
        temp = get_rep(where, x)
        if isinstance(temp, list):
            return temp
        # print(parsed[x])
        name, arg = temp
        name_set.add(name)
        var_dic[x] = name
        return name, arg

    class Scope:
        def __init__(self, x, where=""):
            self.index = x
            def_index = get_def(x)
            self.cdef = []
            self.inst = get_inst(x)
            self.imp = get_import(x)
            for _ in self.imp:
                children = parsed[_]["children"]
                for child in children:
                    assert parsed[child]["type"] == "alias"
                    name_set.add(parsed[child]["value"])
            self.graph = []
            for _ in self.inst:
                if parsed[_]["type"] == "Assign":
                    temp = represent(where, parsed[_]["children"][-1])
                    if isinstance(temp, tuple):
                        name, arg = temp
                    for var in parsed[_]["children"][-2::-1]:
                        if isinstance(temp, list):
                            # print(parsed[var])
                            name, arg = represent(where, var)
                            arg += temp
                            temp = 0
                        else:
                            _name = name
                            _arg = arg
                            ttemp = represent(where, var)
                            if isinstance(ttemp, list):
                                arg += ttemp
                            else:
                                name, arg = ttemp
                                arg.append((_name, _arg))
                    self.graph.append((parsed[_]["lineno"], name, arg))
                if parsed[_]["type"] in ["Expr", "UnaryOp", "Return"]:
                    if parsed[parsed[_]["children"][0]]["type"] == "Call":
                        name, arg = represent(where, parsed[_]["children"][0])
                        self.graph.append((parsed[_]["lineno"], name, arg))
            # print(where)
            global event_graph
            event_graph += self.graph
            for _ in def_index:
                self.cdef.append(
                    (
                        _,
                        parsed[_]["value"],
                        parsed[_]["children"][0],
                        Scope(parsed[_]["children"][1], parsed[_]["value"] + "::"),
                    )
                )

    module = Scope(0)
    # print(name_set)
    # or _ in event_graph:
    # S    print(_)

    nodes = []
    edges = []
    not_event = {}

    def get_edge(x):
        idx, name, args = x
        pos = len(nodes)
        nodes.append(name)
        if "." in name or "[" in name or "(" in name:
            pass
        else:
            if name in not_event:
                pos = not_event[name]
            else:
                not_event[name] = pos
        for arg in args:
            edges.append((idx, pos, get_edge((idx, arg[0], arg[1]))))
        return pos

    for _ in event_graph:
        # print(_)
        get_edge(_)

    from collections import deque

    def bfs(graph, start, target):
        visited = set()
        queue = deque([(start, [(nodes[start], -1)])])
        while queue:
            node, path = queue.popleft()
            if node == target:
                return path
            if node in visited:
                continue
            visited.add(node)
            if node in graph:
                neighbors = graph[node]
                for neighbor, lineno in neighbors:
                    queue.append((neighbor, path + [(nodes[neighbor], lineno)]))
        return None

    def has_path(graph, source, san, sink):
        ans = []
        for so in source:
            for si in sink:
                path = bfs(graph, so, si)
                if path:
                    ans.append(path)
        return ans

    graph = {}
    for lineno, end, start in edges:
        if start not in graph:
            graph[start] = []
        graph[start].append((end, lineno))

    def check_node(nodes, rules):
        ans = []
        for i, node in enumerate(nodes):
            for rule in rules:
                if rule in node:
                    ans.append(i)
                    break
        """
        for _ in ans:
            print(nodes[_],end=' ')
        print()
        """
        return ans

    #############하드코딩됨
    source = check_node(nodes, src_rule)
    san = check_node(nodes, san_rule)
    sink = check_node(nodes, snk_rule)

    # print(nodes)

    def find_pos(line, node):
        if "::" in node:
            node = node[node.rfind("::") + 2 :]
        node = re.escape(node)
        node = node.replace("\\(\\)", "\\(.*?\\)")
        regex = re.compile(node)
        return re.search(regex, line).span()

    san_nodes = [nodes[_] for _ in san]
    result = has_path(graph, source, san, sink)
    for path in result:
        print([_[0] for _ in path])
        lineno_path = [_[1] for _ in path[1:]]
        for i, lineno in enumerate(lineno_path):
            print(lineno, source_code[lineno - 1])
            print(
                find_pos(source_code[lineno - 1], path[i][0]),
                find_pos(source_code[lineno - 1], path[i + 1][0]),
            )
        path_san = []
        for i, _ in enumerate(path):
            if _[0] in san_nodes:
                path_san.append((i, _[0]))
        print(path_san)
        print("\n")
