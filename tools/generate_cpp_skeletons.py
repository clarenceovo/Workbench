import ast, os, sys, re, textwrap

PYTHON_ROOT = sys.argv[1] if len(sys.argv) > 1 else 'Workbench'
CPP_ROOT = sys.argv[2] if len(sys.argv) > 2 else 'WorkbenchCpp'

TYPE_MAP = {
    'int': 'int64_t',
    'float': 'double',
    'str': 'std::string',
    'bool': 'bool',
    'datetime': 'std::chrono::system_clock::time_point',
}

def map_type(ann):
    if isinstance(ann, ast.Subscript):
        if getattr(ann.value, 'id', '') == 'list' and isinstance(ann.slice, ast.Name):
            elem = map_type(ann.slice)
            return f'std::vector<{elem}>'
        elif getattr(ann.value, 'id', '') == 'Optional' and isinstance(ann.slice, ast.Name):
            return map_type(ann.slice)
    elif isinstance(ann, ast.Name):
        return TYPE_MAP.get(ann.id, 'std::string')
    elif isinstance(ann, ast.Attribute):
        return TYPE_MAP.get(ann.attr, 'std::string')
    return 'std::string'


def process_file(py_file, cpp_base):
    with open(py_file, 'r') as f:
        source = f.read()
    try:
        tree = ast.parse(source, filename=py_file)
    except SyntaxError:
        return
    classes = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            is_dataclass = any(
                (isinstance(d, ast.Name) and d.id == 'dataclass') or
                (isinstance(d, ast.Attribute) and d.attr == 'dataclass')
                for d in node.decorator_list
            )
            if not is_dataclass:
                continue
            fields = []
            for stmt in node.body:
                if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                    fields.append((stmt.target.id, map_type(stmt.annotation)))
            classes.append((node.name, fields))
    if not classes:
        return
    # produce header file
    rel_path = os.path.relpath(py_file, PYTHON_ROOT)
    base_name = os.path.splitext(rel_path)[0]
    dir_name = os.path.join(cpp_base, os.path.dirname(base_name))
    os.makedirs(dir_name, exist_ok=True)
    header_path = os.path.join(cpp_base, base_name + '.h')
    with open(header_path, 'w') as h:
        guard = re.sub(r'[^A-Za-z0-9]', '_', base_name).upper() + '_H'
        h.write(f'#ifndef {guard}\n#define {guard}\n\n')
        h.write('#include <string>\n#include <vector>\n#include <chrono>\n#include <cstdint>\n\n')
        for cls_name, fields in classes:
            h.write(f'struct {cls_name} {{\n')
            for name, ctype in fields:
                h.write(f'    {ctype} {name};\n')
            h.write('};\n\n')
        h.write(f'#endif // {guard}\n')


def main():
    for root, _, files in os.walk(PYTHON_ROOT):
        for file in files:
            if file.endswith('.py'):
                process_file(os.path.join(root, file), CPP_ROOT)

if __name__ == '__main__':
    main()
