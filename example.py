import lib

#
#  x = prompt('enter a number')
#  y = parseInt(x, 10) ** 7
#  alert('your number was ' + x + ' and its seventh power is ' + y)
#
# -- would compile to --
#
#  a=prompt('enter a number');alert('your number was '+a+' and its seventh power is '+Math.pow(parseInt(a,10),7));
#

prompt = lib.jsfunc('prompt')
parseInt = lib.jsfunc('parseInt')
alert = lib.jsfunc('alert')


def __main():
    x = prompt('enter a number')
    y = parseInt(x, 10) ** 7
    alert('your number was ' + x + ' and its seventh power is ' + y)
    with lib.if_(y > 1000):
        alert('and that is quite large')


print(lib.codegen(__main))
