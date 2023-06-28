# pyjs

Write JavaScript directly in Python!

```py
from pyjs import jsfunc, if_, elseif, codegen

querySelector = jsfunc('document.querySelector')
log = jsfunc('console.log')

def func():
    elem = querySelector('#myinput')

    with if_(elem.value == 'hello'):
        elem.value = 'hi there'

    with elseif(elem.value.startsWith('i\'m ')):
        elem.value = 'hi ' + elem.value.substring(len('i\'m ')) + ', i\'m dad'

        log('i can also do math btw:', (elem.value.length ** 7) //
            4 > 127 - elem.value.charAt(0) / 1.5)

print(codegen(func))
```

outputs:

<!--prettier-ignore-->
```js
let a=document.querySelector("#myinput");if(a.value==="hello"){a.value="hi there";}else if(a.value.startsWith("i'm ")){a.value="hi "+a.value.substring(4)+", i'm dad";console.log("i can also do math btw:",Math.floor(Math.pow(a.value.length,7)/4)>(127-(a.value.charAt(0)/1.5)));}
```

or pretty-printed _(note that prettier also removed a few unnecessary parentheses that this library added because i'm not gonna figure out all the rules behind javascript operator precedence)_:

```js
let a = document.querySelector("#myinput");
if (a.value === "hello") {
  a.value = "hi there";
} else if (a.value.startsWith("i'm ")) {
  a.value = "hi " + a.value.substring(4) + ", i'm dad";
  console.log(
    "i can also do math btw:",
    Math.floor(Math.pow(a.value.length, 7) / 4) > 127 - a.value.charAt(0) / 1.5
  );
}
```

### status

code is really fucking awful right now but this is just a gimmick

not but like seriously, close your eyes while reading the code.
