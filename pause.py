__author__ = 'Mathias Zechmeister'
__version__ = '2017-02-08'

import inspect
import pdb
import sys
import termios

def getch():
   """Read immediately a character without enter.
   >>> print 'char:',; ch = getch(); print 'nextline'
   """
   old_settings = termios.tcgetattr(0)
   new_settings = old_settings[:]
   new_settings[3] &= ~termios.ICANON #& ~termios.ECHO
   try:
      termios.tcsetattr(0, termios.TCSANOW, new_settings)
      ch = sys.stdin.read(1)
   finally:
      termios.tcsetattr(0, termios.TCSANOW, old_settings)
   return ch

def pause(*args, **kwargs):
   """
   Set a pause at the current location in the script.

   Pause waits for a character. If the character is a 'd' or 'n', it enters python debug
   mode. If it is a 'q', it quits the program. An enter or any other characters continues.

   Parameters
   ----------
   args : optional
      Arguments to print.
   ch : optional
      A character can be passed, otherwise it prompts for it.
   depth : optional
      Stack level where to pause (default=0).

   Example
   -------
   >>> from pause import pause
   >>> def func_a():
   >>>    a = 2
   >>>    pause()
   >>>    b = 3
   >>>    pause()
   >>>
   >>> func_a()

   """
   #lineno = inspect.currentframe().f_back.f_lineno
   depth = 1 + kwargs.get('depth', 0)   # we want to stop in the caller
   _, filename, lineno, _,_,_ = inspect.stack()[depth]
   ch = kwargs.get('ch')
   if ch:
      print 'stop ', filename, ' line', lineno, ':', " ".join(map(str,args))
   else:
      prompt = 'pause %s line %s: %s ' % (filename, lineno, " ".join(map(str,args)))
      # print prompt,   # supress newline, but leaves a residual white space
      sys.stdout.write(prompt)
      ch = getch()  # all shells?
      if ch != '\n': print
      #ch = sys.stdin.readline()  # requires manual enter
      #ch = os.popen('read -s -n 1 -p "'+prompt+'" ch; echo $ch').read()   # only bash?
      #print ch.rstrip()   # print single char (and remove newline)

   if ch == 'q':
      exit()
   elif ch in ('d', 'n'):
      print "debug mode; type 'c' to continue"
      if 1:
         # a workaround for bad arrow keys and history behaviour
         print 'mode d:  logging turned off, stdout reseted'
         sys.stdout = sys.__stdout__
      x = pdb.Pdb(skip=['pause'])
      x.prompt = 'Bla '
      # x.rcLines=["print 'aa'"]; x.setup(sys._getframe().f_back,None)
      # x.set_trace(sys._getframe().f_back) #debug
      x.set_trace(sys._getframe(depth)) #debug
   return ch

def stop(*args):
   pause(*args, ch='d', depth=1)
