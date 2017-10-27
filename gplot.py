# gplot v06 2016-08-08
# A python gnuplot interface
# by Mathias Zechmeister

from __future__ import print_function
import subprocess
from numpy import savetxt
import tempfile
import os

__author__ = 'M. Zechmeister'
__version__ = 'v07'

path = os.path.dirname(__file__)

if 'pid' not in globals():
   global pid
   pid = 0

og = 0  # overplot number
buf = ''
tmp2 = []

def gplot_init(stdout=False):
   '''Open the gnuplot pipe'''
   global pid, gnuplot, gp, version
   if not pid:
      version = subprocess.check_output(['gnuplot', '-V'])
      version = float(version.split()[1])
      gp = print
      gnuplot = type('gnuplot',(),{'pid':None})
      if not stdout:
         gnuplot = subprocess.Popen(['gnuplot','-p'], shell=True, stdin=subprocess.PIPE,
                universal_newlines=True, bufsize=0)  # This line is needed for python3! Unbuffered and to pass str instead of bytes
         gp = gnuplot.stdin.write
      if version in [4.6]: gp('set term wxt') # Prefer wxt over qt. Still possible in 4.6
      gp('load "%s"\n'%os.path.join(path,"zoom.gnu")) # preload
   pid = gnuplot.pid
   #print pid

def iplot(*args, **kargs):
   '''Plotting in Jupyter'''
   # import sys
   # sys.path.append('/home/zechmeister/caveman/pub/zechmeister/python/gplot.py')
   # from gplot import *
   # Example:  iplot('sin(x)')
   outfile = tempfile.NamedTemporaryFile(suffix='.png').name
   #outfile = tempfile.NamedTemporaryFile().name+'.png'
   gplot_init()

   gp('set term pngcairo; set out "'+outfile+'"\n')
   gplot(*args,**kargs)
   gp('set term pngcairo; set out\n')

   #return {'filename':outfile, 'format':'png'}
   # wait until the figure is written to file and the file is closed
   import time, os
   counter = 0
   while counter<100 and (not os.path.exists(outfile) or os.system("lsof "+outfile)==0):
      time.sleep(0.003)
      counter += 1
      print(counter, end='\r')
   print(counter, outfile, os.path.exists(outfile), os.system("lsof "+outfile))

   from IPython.display import Image
   return Image(outfile, format='png')

def gplot(cmd='', y='', e='', w='', w1='', w2='', w3='', w4='', w5='', w6='', pl='pl ', tmp=None, flush="\n", stdout=False):
#def gplot(*cols, **kwargs={w:'',pl:'pl',tmp:'',flush:"\n"}):
   """
   Parameters
   ----------
   cmd : array or str for function, file, or other plot commands like style
   pl : str, optional
       leading command (default: 'plot', can be changed to replot or splot)
   tmp : str, optional
       None - create a non-persistent temporary file (default)
       '' - create a local persistent temporary file
       '-' - use gnuplot special filename (no interactive zoom available)
       'filename' - create manually a temporary file
   flush : str, optional
       set to '' to suppress flush until next the ogplot (for large data sets)
   stdout : boolean, optional
       if true plot commands are send to stdout instead to gnuplot pipe

   Examples
   --------
   >>> gplot('sin(x) w lp lt 3')
   >>> ogplot(numpy.arange(10)**2.,'w lp lt 3')
   >>> ogplot('"filename" w lp lt 3')
   >>> gplot('x/5, 1, x**2/50 w l lt 3,', numpy.sqrt(numpy.arange(10)),' us 0:1 ps 2 pt 7 ,sin(x)')
   """
   global gpflush, og, buf # implicite globals: tmp2,gp,pid,version
   gplot_init(stdout)

   if version in [4.6] and flush=="\n": flush = "\n\n" # append a newline to workaround a gnuplot pipe bug
   # with mouse zooming (see http://sourceforge.net/p/gnuplot/bugs/1203/)

   if pl=='pl ': og = 0; buf = ''; gp('\n')        # reset
   elif pl=='repl ' and gpflush=='': pl = ','
   gpflush = flush
   data = ()
   for arg in [cmd,y,e,w,w1,w2,w3,w4,w5,w6,flush]:
      #print og,type(arg), arg
      if type(arg)==str:   # append argument, but flush the data before
         if len(data):
            data = zip(*data) if len(data)>1 else data[0]
            tmpname = tmp
            if tmp in ('-',):   # use gnuplot's special filename '-'
               buf += "\n".join(" ".join(map(str,tup)) for tup in data)+"\ne\n"
            elif tmp==None:     # create temporary file; default
               tmp2.append(tempfile.NamedTemporaryFile())
               tmpname = tmp2[-1].name
               #savetxt(tmp2[-1], data) #zipped data not supported by python3
               savetxt(tmp2[-1], list(data)) # zipped data not supported by python3
               tmp2[-1].seek(0)
            else:               # create local temporary file
               if tmp=='':
                  tmpname = 'gptmp_'+str(pid)+str(og)
                  og += 1
               savetxt(tmpname, data)
            pl += '"'+tmpname+'"'
         pl += ' ' + arg
         data = ()
      else:   # collect data
         data += (arg,)
   #print pl+buf
   gp(pl if flush=='' else pl+buf)


def ogplot(*args,**kargs):   # overplot command
   gplot(*args, pl='repl ', **kargs)

def gplot_set(cmd):
   # can be emulated by gplot(pl='')
   gplot_init()
   gp(cmd+"\n")
