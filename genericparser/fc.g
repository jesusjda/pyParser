// fc language based on json
start:dict
CMP: "<="|"=>"|"=<"|"=="|">="|">"|"<"|"="
SUM: "+" | "-"
MUL: "*" | "/" 

CNAME: ("_"|LETTER) ("_"|LETTER|DIGIT|"'"|"^"|"!"|".")*
 
term: [SUM] NUMBER | [SUM] CNAME | "(" expression ")"
factor: term (MUL term)*
expression:  factor (SUM factor)*

constraint: expression CMP expression
name: CNAME
string: ESCAPED_STRING
bool: "true" | "false"
null: "null"
_value: dict
     | list
     | string
     | expression
     | constraint
     | bool
     | null


key: CNAME | NUMBER | ESCAPED_STRING
!namekey : "source" | "target"  | "name"  | "initnode" | "domain"
!lvarskey : "vars" | "pvars"

list : "[" [_value ("," _value)* ","?]  "]"
lvars : "[" [name ("," name)* ","?] "]"
dict : "{" [pair ("," pair)* ","?] "}"
pair : key ":" _value
     | namekey ":" name
     | lvarskey ":" lvars


COMMENT: /\/\*([^*]*|([^*]*\*+[^*\/]+)*)\*+\//
       | "//" /[^\n]*/
       | /#[^\n]*/

%import common.ESCAPED_STRING
%import common.NUMBER
%import common.LETTER
%import common.WORD
%import common.DIGIT
%import common.WS
%ignore WS
%ignore COMMENT
