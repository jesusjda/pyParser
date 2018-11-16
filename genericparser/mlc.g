// mlc language

start: _program

_endls: "\n"+

CMP: "<="|"=>"|"=<"|"=="|">="|">"|"<"|"="
SUM: "+" | "-"
MUL: "*" | "/" 

CNAME: ("_"|LETTER) ("_"|LETTER|DIGIT|"'"|"^"|"!"|".")*
name: CNAME

term: [SUM] NUMBER | [SUM] CNAME | "(" expression ")"
factor: term (MUL term)*
expression:  factor (SUM factor)*

constraint: expression CMP expression

transition: "!path" _endls (constraint _endls)+

transitions: (transition)+

vars: (name)+
pvars: (name)+

_program: _endls? "!vars" _endls vars _endls ("!pvars" _endls pvars _endls)? transitions

COMMENT: /\/\*([^*]*|([^*]*\*+[^*\/]+)*)\*+\//
       | "//" /[^\n]*/
       | /#[^\n]*/

%import common.NUMBER
%import common.LETTER
%import common.WORD
%import common.DIGIT
%ignore " "
%ignore "\t"
%ignore "\r"
%ignore COMMENT