start:constraint
CMP: "<="|"=>"|"=<"|"=="|">="|">"|"<"|"="
SUM: "+" | "-"
MUL: "*" | "/"

CNAME: ("_"|LETTER) ("_"|LETTER|DIGIT|"'"|"^"|"!")*

term: [SUM] NUMBER | [SUM] CNAME | "(" expression ")"
factor: term (MUL term)*
expression:  factor (SUM factor)*

constraint: expression CMP expression

%import common.NUMBER
%import common.LETTER
%import common.DIGIT
%import common.WS
%ignore WS