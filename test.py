from lib import *

prompt = jsfunc('prompt')
parseInt = jsfunc('parseInt')
alert = jsfunc('alert')
log = jsfunc('console.log')


def x():
    a = prompt('enter a number')
    b = parseInt(a, 7)-9+9
    alert(text := 'original: ' + a + ', parsed base 7: ' + b)
    log(text)
    d = c = b
    d += 1
    c += 2
    alert(c//2 + ', ' + d**2)

    with if_(d**3 > 1000):
        alert('d cubed is largeass')

    with elseif(d == 0):
        alert('thats lame.')

    with elseif(d < 0):
        alert('wtf how did that happen??')

    with else_():
        alert('?')

    # proposed syntax for ternary: if_(...).then(...).else_(...)

    # officially proposed by me

    # right here

    # right now


querySelector = jsfunc('document.querySelector')
log = jsfunc('console.log')


def y():
    elem = querySelector('#myinput')

    with if_(elem.value == 'hello'):
        elem.value = 'hi there'

    with elseif(elem.value.startsWith('i\'m ')):
        elem.value = 'hi ' + elem.value.substring(len('i\'m ')) + ', i\'m dad'

        log('i can also do math btw:', (elem.value.length ** 7) //
            4 > 127 - elem.value.charAt(0) / 1.5)


with open('_test.js', 'w') as f:
    print(js := codegen(y))
    f.write(js)
