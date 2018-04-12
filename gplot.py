# A python gnuplot interface

from __future__ import print_function
import subprocess
from numpy import savetxt
import tempfile
import os

__author__ = 'Mathias Zechmeister'
__version__ = 'v08'
__date__ = '2018-03-09'
__all__ = ['Iplot', 'gplot', 'Gplot', 'ogplot']

#path = os.path.dirname(__file__)

class Gplot(object):
   """The interface between Python and gnuplot.
   
   Parameters
   ----------
   args : array or str for function, file, or other plot commands like style
   tmp : str, optional
       None - create a non-persistent temporary file (default)
       '' - create a local persistent file
       '-' - use gnuplot special filename (no interactive zoom available,
             replot does not work)
       '$' - use inline datablock (not faster than temporary data,
             does not work with flush='' an ogplot)
       'filename' - create manually a temporary file
   flush : str, optional
       set to '' to suppress flush until next the ogplot (for large data sets)
   stdout : boolean, optional
       if true plot commands are send to stdout instead to gnuplot pipe

   pl : str, optional
       leading command (default: 'plot', can be changed to replot or splot)
   calling with a gnuplot set attribute return the same instance. This allows to chain calls.

   Examples
   --------
   >>> gplot('sin(x) w lp lt 3')
   >>> ogplot(numpy.arange(10)**2.,'w lp lt 3')
   >>> ogplot('"filename" w lp lt 3')
   >>> gplot('x/5, 1, x**2/50 w l lt 3,', numpy.sqrt(numpy.arange(10)),' us 0:1 ps 2 pt 7 ,sin(x)')
   >>> gplot.mxtics().mytics(2).repl
   >>> gplot([1,2,3,4])
   >>> gplot([1,2,3,4], [2,2,1,1.5])
   >>> gplot([1,2,3,4], [[2,2,1,1.5], [3,1,4,5.5]])
   >>> gplot([[2,2,1,1.5]])
   >>> gplot([1],[2],[3],[4])
   >>> gplot(1,2,3,4)
   >>> gplot([1,2,1,0.5])
   >>> gplot([[2,2,1,1.5]])
   
   """
   version = subprocess.check_output(['gnuplot', '-V'])
   version = float(version.split()[1]) 
   
   def __init__(self, stdout=False, tmp=None, mode='plot'):
      self.stdout = stdout
      self.tmp = tmp
      self.mode = getattr(self, mode) # set the default mode (plot, splot)
      self.gnuplot = subprocess.Popen(['gnuplot','-p'], shell=True, stdin=subprocess.PIPE,
                   universal_newlines=True, bufsize=0)  # This line is needed for python3! Unbuffered and to pass str instead of bytes
      self.pid = self.gnuplot.pid
      #if version in [4.6]: gp('set term wxt;') # Prefer wxt over qt. Still possible in 4.6
      #gp('load "%s"\n'%os.path.join(path,"zoom.gnu")) # preload
      self.og = 0  # overplot number
      self.buf = ''
      self.tmp2 = []
      self.flush = None
   
   def _plot(self, *args, **kwargs):
      # collect all argument
      tmp = kwargs.pop('tmp', self.tmp)
      flush = kwargs.pop('flush', '\n')
      if self.version in [4.6] and flush=="\n": flush = "\n\n" # append a newline to workaround a gnuplot pipe bug
      # with mouse zooming (see http://sourceforge.net/p/gnuplot/bugs/1203/)
      self.flush = flush
      pl = ''
      data = ()
      for arg in args+(flush,):
         if isinstance(arg, str):   # append argument, but flush the data before
            if data:
               # transpose data when writing
               self.og += 1
               data = zip(*data)
               tmpname = tmp
               if tmp in ('-',):
                  # use gnuplot's special filename '-'
                  self.buf += "\n".join(" ".join(map(str,tup)) for tup in data)+"\ne\n"
               elif tmp in ('$',):
                  # gnuplot's inline datablock
                  tmpname = "$data" + str(self.og)
                  # prepend the datablock
                  pl = tmpname+" <<EOD\n"+("\n".join(" ".join(map(str,tup)) for tup in data))+"\nEOD\n" + pl
               elif tmp is None:
                  # create temporary file; default
                  self.tmp2.append(tempfile.NamedTemporaryFile())
                  tmpname = self.tmp2[-1].name
                  #savetxt(tmp2[-1], data) #zipped data not supported by python3
                  savetxt(self.tmp2[-1], list(data), fmt="%s") # zipped data not supported by python3, fmt="%s" to allow for strings
                  self.tmp2[-1].seek(0)
               else:
                  # create local temporary file
                  if tmp=='':
                     tmpname = 'gptmp_'+str(self.pid)+str(self.og)
                  savetxt(tmpname, data)
               pl += '"'+tmpname+'"'
            pl += ' ' + arg
            data = ()
         else:   
            # collect data; append columns and matricies
            _2D = hasattr(arg, '__iter__') and hasattr(arg[0], '__iter__')
            data += tuple(arg) if _2D else (arg,)
      self.put(pl if flush=='' else pl+self.buf, end='')
   def put(self, *args, **kwargs):
      # send the commands to gnuplot
      print(file=None if self.stdout else self.gnuplot.stdin, *args, **kwargs)
      return self
   # some plot commands (kwargs possible)
   def plot(self, *args, **kwargs):
      self.og = 0; self.buf = ''; self.put('\n')        # reset
      return self._plot('plot', *args, **kwargs)
   def splot(self, *args, **kwargs):
      self.og = 0; self.buf = ''; self.put('\n')        # reset
      return self._plot('splot', *args, **kwargs)
   def replot(self, *args, **kwargs):
      return self._plot('replot', *args, **kwargs)
   def oplot(self, *args, **kwargs):
      pl = ',' if self.flush=='' else 'replot '
      return self._plot(pl, *args, **kwargs)
   
   def __call__(self, *args, **kwargs):
      # by default plot mode is executed, but the user can change that
      return self.mode(*args, **kwargs)
   
   def __getattr__(self, name):
      # generic translatation, e.g. gplot.title sends "set title"
      if name in ('__repr__', '__str__'):
         raise AttributeError 
      elif name=='repl':
         return self.replot()
      elif name in ['set', 'unset', 'reset', 'print', 'bind']:
         # some fixed keywords
         # print as attribute does not work in python 2
         def func(*args):
            return self.put(name, *args)
         return func
      else:   
         def func(*args):
            return self.set(name, *args)
         return func
      
class Iplot(Gplot):
   '''
   Jupyter
   Similar as Gplot, but plot returns an object that can be displayed rather than self
   '''
   def __init__(self, *args, **kwargs):   #, cleanup=True, uri=False
      self.suffix = kwargs.pop('imgfile', 'png')
      self.uri = kwargs.pop('uri', False)
      self.cleanup = kwargs.pop('cleanup', True)
      return super().__init__(*args, **kwargs)

   def _plot(self, *args, **kwargs):
      term = {'svg': 'svg mouse standalone', 
              'html': 'canvas name "fishplot" mousing jsdir "gp/"'
             }.get(self.suffix, 'pngcairo')
      imgfile = tempfile.NamedTemporaryFile(suffix='.'+self.suffix).name
      if self.suffix=='html':
         imgfile = "gnuplot_canvas.js"

      self.term(term).out('"%s"'%imgfile)
      super()._plot(*args, **kwargs)
      self.out()

      import time, os
      counter = 0
      while counter<100 and not (os.path.exists(imgfile) and os.system("lsof "+imgfile)):
         time.sleep(0.003)
         counter += 1
         if not self.cleanup: print(counter, end='\r')   
      if not self.cleanup:                                                                                                                  
         print(counter, imgfile, os.path.exists(imgfile), os.system("lsof "+imgfile))                                                              
                                                                                                                                                
      from IPython.display import Image, SVG, HTML, Javascript
      if self.uri:                                                                                                                                      
         import base64                                                                                                                             
         im = 'data:image/png;base64,'+base64.b64encode(open(imgfile, "rb").read()).decode('ascii') 
         showfunc = Image
      else:                                                                                                                                        
         showfunc = {'svg':SVG, 'html':HTML}.get(self.suffix, Image) 
         if self.suffix=='html':
            #ct = open("gp/canvastext.js").read()
            #gc = open("gp/gnuplot_common.js").read()
      #fp = open("gnuplot_canvas.js").read()
      #  <script>%s</script>
      # <script>%s</script>
      # <script>fishplot();</script>
            imgfile='''
 <table class="mbleft"><tbody><tr><td class="mousebox">
<table class="mousebox" border="0">
  <tbody><tr><td class="mousebox">
    <table class="mousebox" id="gnuplot_mousebox" border="0">
    <tbody><tr><td class="mbh"></td></tr>
    <tr><td class="mbh">
      <table class="mousebox">
	<tbody><tr>
	  <td class="icon"></td>
	  <td class="icon" onclick="gnuplot.toggle_grid"><img src="gp/grid.png" id="gnuplot_grid_icon" class="icon-image" alt="#" title="toggle grid"></td>
	  <td class="icon" onclick="gnuplot.unzoom"><img src="gp/previouszoom.png" id="gnuplot_unzoom_icon" class="icon-image" alt="unzoom" title="unzoom"></td>
	  <td class="icon" onclick="gnuplot.rezoom"><img src="gp/nextzoom.png" id="gnuplot_rezoom_icon" class="icon-image" alt="rezoom" title="rezoom"></td>
	  <td class="icon" onclick="gnuplot.toggle_zoom_text"><img src="gp/textzoom.png" id="gnuplot_textzoom_icon" class="icon-image" alt="zoom text" title="zoom text with plot"></td>
	  <td class="icon" onclick="gnuplot.popup_help()"><img src="gp/help.png" id="gnuplot_help_icon" class="icon-image" alt="?" title="help"></td>
	</tr>
	<tr>
	  <td class="icon" onclick="gnuplot.toggle_plot(&quot;gp_plot_1&quot;)">1</td>
	  <td class="icon"> </td>
	  <td class="icon"> </td>
	  <td class="icon"> </td>
	  <td class="icon"> </td> 
	  <td class="icon"> </td>
	</tr>
      </tbody></table>
  </td></tr>
</tbody></table></td></tr><tr><td class="mousebox">
<table class="mousebox" id="gnuplot_mousebox" border="1">
<tbody><tr> <td class="mb0">x&nbsp;</td> <td class="mb1"><span id="gnuplot_canvas_x">-3.386</span></td> </tr>
<tr> <td class="mb0">y&nbsp;</td> <td class="mb1"><span id="gnuplot_canvas_y">-0.4144</span></td> </tr>
</tbody></table></td></tr>
</tbody></table>
</td><td>
<table class="plot">
<tbody><tr><td>
    <canvas id="fishplot" width="600" height="400" tabindex="0">
	Sorry, your browser seems not to support the HTML 5 canvas element
    </canvas>
</td></tr>
</tbody></table>
</td></tr></tbody></table>         
        <script src="gp/canvastext.js"></script>
         <script src="gp/gnuplot_common.js"></script>
         <script src="gp/gnuplot_mouse.js"></script>
         <script src="gnuplot_canvas.js"></script>
         <script>
            fishplot();
              $('body').on('contextmenu', '#fishplot', function(e){ return false; });
       </script>
            '''
      if self.cleanup:                                                                                                                                  
         os.system("rm -f "+imgfile)                                                                                                               
      #return im                                                                                                                                    
      #   print(counter, end='\r')
      #print(counter, imgfile, os.path.exists(imgfile), os.system("lsof "+imgfile))

      return showfunc(imgfile)

# a default instance
gplot = Gplot()
ogplot = gplot.oplot


