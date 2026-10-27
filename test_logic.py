import importlib.util, sys, types, io
# Test pure ID decoding by extracting source via AST while stubbing streamlit/pandas/PIL/EasyOCR dependencies
import ast
src=open("app.py",encoding="utf-8").read()
tree=ast.parse(src)
nodes=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.Assign)) and (getattr(n,"name",None) in ("western_digits","decode_national_id") or isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="GOVERNORATES" for t in n.targets))]
ns={"re":__import__("re"),"date":__import__("datetime").date}
exec(compile(ast.Module(body=nodes,type_ignores=[]),"app.py","exec"),ns)
assert ns["western_digits"]("١٢٣٤٥٦")=="123456"
assert ns["decode_national_id"]("29901011200013")[3] == "" # valid-format date: 1999-01-01, governorate 12
assert ns["decode_national_id"]("39902311200013")[3] != "" # invalid date
assert ns["decode_national_id"]("123")[3] != ""
print("PASS: syntax and ID parsing tests")
