// koat
start: _program

CMP: "<="|"=>"|"=<"|"=="|">="|">"|"<"|"="
SUM: "+" | "-"
MUL: "*" | "/" 

CNAME: ("_"|LETTER) ("_"|LETTER|DIGIT|"'"|"^"|"!")*
 
term: [SUM] NUMBER | [SUM] CNAME | "(" expression ")"
factor: term (MUL term)*
expression:  factor (SUM factor)*

constraint: expression CMP expression

name: CNAME
number: NUMBER

_goal: "(" "GOAL" name ")"
_startterm: "(" "STARTTERM" entry ")"

entry: "CONSTRUCTOR-BASED" -> noentry
     | "(" "FUNCTIONSYMBOLS" name ")"

variables: "(" "VAR" name* ")"

node: name "(" (expression ("," expression)*)? ")"
_and: "&&" | "/\\"
constraints: ("[" constraint ( _and constraint)* "]")
           | (":|:" constraint ( _and constraint)*)

_right_hand: node
          | ("Com_1" "(" node ")")


rule: node "->" _right_hand constraints?

rules: "(" "RULES" rule* ")" 

_program: _goal _startterm variables rules

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