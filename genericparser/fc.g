// fc language based on json
start:dict
CMP: "<="|"=>"|"=<"|"=="|">="|">"|"<"|"="
SUM: "+" | "-"
MUL: "*" | "/" 

CNAME: ("_"|LETTER) ("_"|LETTER|DIGIT|"'"|"^"|"!")*
 
term: [SUM] NUMBER | [SUM] CNAME | "(" expression ")"
factor: term (MUL term)*
expression:  factor (SUM factor)*

constraint: expression CMP expression
name: CNAME
number: SIGNED_NUMBER
string: ESCAPED_STRING
bool: "true" | "false"
null: "null"
_value: dict
     | list
     | name
     | string
     | number
     | constraint
     | bool | null


key: CNAME | NUMBER | ESCAPED_STRING


list : "[" [_value ("," _value)* ","?]  "]"

dict : "{" [pair ("," pair)* ","?] "}"
pair : key ":" _value


COMMENT: /\/\*([^*]*|([^*]*\*+[^*\/]+)*)\*+\//
       | "//" /[^\n]*/
       | /#[^\n]*/

%import common.ESCAPED_STRING
%import common.SIGNED_NUMBER
%import common.NUMBER
%import common.LETTER
%import common.WORD
%import common.DIGIT
%import common.WS
%ignore WS
%ignore COMMENT