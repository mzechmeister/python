from __future__ import print_function

import subprocess
import numpy as np

try:
   import pyfits
except:
   import astropy.io.fits as pyfits

__author__ = 'Mathias Zechmeister'
__version__= '2.21'
__date__ = '2020-05-01'



class DS9:
   def __call__(self, *args, **kwargs):
       _ds9(*args, **kwargs)
   def line(self, *args, **kwargs):
       ods9(*args, line=True, **kwargs)
   def box(self, *args, **kwargs):
       ods9(*args, box=True, **kwargs)
   def circle(self, *args, **kwargs):
       ods9(*args, circle=True, **kwargs)
   def msk(self, *args, **kwargs):
       ds9msk(*args, **kwargs)
   def set(self, arg1, arg2='', port='pyds9'):
#      for arg in args:
         subprocess.call('xpaset -p '+port+' '+arg1+' '+arg2, shell=True)
   def __getattr__(self, name):
      # generic translatation, e.g. ds9.cmap sends "cmap"
      if name in ('__repr__', '__str__'):
         raise AttributeError
      else:
         # dynamic attributes (xlabel, key, etc.)
         def func(*args):
            return self.set(name, *args)
         return func


ds9 = DS9()

def _ds9(data, tmpfile='-', port='pyds9'):
   """
   Pipes data and commands to ds9.

   Parameters
   ----------
   data : array_like or string
   tmpfile : string
       If '-' (default) data are sent directly to ds9.
       Otherwise a local file tmp.fits is created.

   Examples:
   ---------
   >>> from ds9 import *
   >>> import numpy as np
   >>> arr = np.arange(20).reshape(5,4)
   >>> ds9(arr)

   """
   # check if the port exists or create a new instance
   if type(data) is str:
      tmpfile = data
   elif tmpfile=='-':
      # data.T because fortran-like
      dim = ",".join("%sdim=%i" % b for b in zip(('x','y','z'),data.T.shape))
      dim += ",bitpix=%i" % {'bool':8, 'int64':64, 'int32':32, 'uint16':16,'float64':-64, 'float32':-32}[data.dtype.name]
      endian = data.dtype.byteorder
      if endian in '<>':
         dim += ",endian=[%s]" % {'<':'little', '>':'big'}[endian]
      #pipeds9 = subprocess.Popen(['xpaset', port,'array', '-', dim], shell=True, stdin=subprocess.PIPE,)
      #pipeds9 = subprocess.Popen(['cat - > tmp1'], shell=True, stdin=subprocess.PIPE,)
      #data.tofile('tmp1')
      #pipeds9.stdin.close()
   else:
      tmpfile = 'tmp.fits'
      hdu = pyfits.PrimaryHDU(data)
      hdu.writeto(tmpfile, clobber=True)
      subprocess.call('xds9 -p '+port+' '+tmpfile+' &', shell=True)

   ports, xpamiss = subprocess.Popen("xpaget xpans | grep 'DS9 "+port+"'", shell=True, stdout=subprocess.PIPE, stderr= subprocess.PIPE, universal_newlines=True, bufsize=0).communicate()

   if ports=='':
      # switch to normal start and create a new port
      if tmpfile=='-':
         pipeds9 = subprocess.Popen(['ds9  -analysis ~/.ds9.ans -title '+port+" -port 0 -array -'["+dim+"]' "], shell=True, stdin=subprocess.PIPE)
#           +ds9opt+"  2> /dev/null &", unit=unit
         # data.tofile(pipeds9.stdin) # raises in python3: "OSError: obtaining file position failed"
         pipeds9.stdin.write(data.tobytes())
         pipeds9.stdin.close()
      else:
         subprocess.call('xds9 -p '+port+' '+tmpfile+' &', shell=True)
   else:
      if tmpfile=='-':
         subprocess.call('xpaset -p '+port+' frame new', shell=True)
         pipeds9 = subprocess.Popen(['xpaset '+port+" array -'["+dim+"']"], shell=True, stdin=subprocess.PIPE)
         #data.tofile(pipeds9.stdin)
         pipeds9.stdin.write(data.tobytes())
         pipeds9.stdin.close()
      else:
         subprocess.call('xds9 -p '+port+' '+tmpfile+' &', shell=True)


def ds9msk(mask, bx=None, by=None, limit=15000, box=True, **kwargs):
   """
   Create a ds9 region from a map and mark bad pixels with boxes.

   Parameters
   ----------
   mask : array-like
      Nonzero values are marked with boxes.
   bx : float
      Box size in x (defaults to 1).
   by : float
      Box size in y (default to bx).

   Examples
   --------
   >>> z = np.arange(20).reshape(5,4)
   >>> ds9(z)
   >>> ds9msk((z % 7)==0) #, clear=True

   """
   idx = np.where(mask)
   if idx[0].size>limit:
      print("WARNING: Too many flagged pixels", idx[0].size, "(limit: %s)"%limit)
      return
   #ods9(*idx, bx, by, box=box, **kwargs)
   ods9(idx[1], idx[0], bx, by, box=box, **kwargs)



def ods9(cx, cy, arg1=None, arg2=None, port='pyds9', frame=None, lastframe=False, reset=False, label=False, tag1=None, tag2=None, regfile=None, color=None, pt=False, box=False, circle=False, curve=False, line=False, point=False, polygon=False, x=False, cross=False, red=False, blue=False, green=False, clear=False, header=[], coord=None, size=None, optsuf=None, offx=None, offy=None):
   """
   Overplot data point in ds9 as a region file

   Parameters
   ----------
   cx :   Data vector
   cy :   Data vector

   Examples
   --------
   Display an array and overplot three points:

   >>> ds9(np.arange(100).reshape(5,20))
   >>> ods9([0,5,2], [0,5,4])

   >>> ods9([0,5,2], [0,5,4], color=['red','blue', 'blue'], clear=True)
   >>> ods9([0,5,2], [0,5,4], blue=True, tag1=['','good','bad'], clear=True)
   >>> ods9([0,5,2], [0,5,4], point='cross', color='yellow', clear=True)

   Print the region file:

   >>> ods9([0,5,2], [0,5,4], color='yellow', point='cross', regfile='-',
   ...              header=['# Region file format: DS9 version 4.0',
   ...                    'global point=cross color=yellow font="helvetica 10 normal" select=1 highlite=1 edit=1 move=1 delete=1 include=1 fixed=0 source', 'image' ])
   ; (coordinate system)

#;
#; OPTIONAL INPUT KEYWORDS:
#;       arg*   - The meaning depends on the selected style.
#;       port   - A named port for an open pipe (address for xpa)
#;       frame  -  Writes to this frame number
#;       /lastframe - Overwrites the last frame
#;       /clear - Deletes all regions
#;       header - a header for the ds9 region file
#;       regfile - Keyword for data transmission
#;                0    direct (bi-directional) pipe (default, not working for some OS)
#;                '-'  pipe via stdin (echo, not working for long input)
#;                filename
#;       ps     - point size (default: 2.5)
#;       color  - color of the elements (vector possible)
#;       pt     - point type (default: circle)
#;                point x y # point=[circle|box|diamond|cross|x|arrow|boxcircle] [size]
#;       curve  - connects points using lines (similar to polygon but not closed)
#;       box    - x y width height angle (default: width=1, height=1)
#;       circle - x y radius (default: radius=2.5)
#;
#;
#; Ellipse
#; Usage: ellipse x y radius radius angle
#;
#; Box
#; Usage: box x y width height angle
#;
#; Polygon
#; Usage: polygon x1 y1 x2 y2 x3 y3 ...
#;
#; Line
#; Usage: line x1 y1 x2 y2 # line=[0|1] [0|1]
#;
#;
#; NOTES:
#;    see ds9.pro for requirements (xpa)
#;-
   """

   #if n_params() lt 2 then message, '% ods9: no data to display'
   #args = str(np.array(cx)+1) + ', ' + str(np.array(cy)+1)
   if not offx: offx = 1 if coord is None else 0
   if not offy: offy = 1 if coord is None else 0

   args = ([x+offx for x in cx], [y+offy for y in cy])

   fmt = "%s,%s"
   opt = type('opt',(),{'arg':(), 'fmt':''})

   #; sarg1=0 means arg1 is of type size/width/length.
   #; sarg1=1 means arg1 is of type position and conversion from IDL-zeros to ds9-one based indexing is done
   #sarg1 = 0
   #sarg2 = 0
   #sarg3 = 0

   if red: color = 'red'
   if blue: color = 'blue'
   if green: color = 'green'

   if box:
      pt = 'box'
      if not arg1: arg1 = 1
      if not arg2: arg2 = arg1
   if circle:
      pt = 'circle'
      if not arg1: arg1 = 2.5
   #if keyword_set(curve) then begin
      #pt = 'line'
      #args = args[0:*] + ',' + args[1:*]
   #endif
   if line:
      pt = 'line'
      args += ([x+offx for x in arg1], [y+offy for y in arg2])
      fmt += ",%s,%s"
      arg1 = arg2 = None

   #if keyword_set(cross) then point = 'cross'
   #if keyword_set(x) then point = 'x'
   #if keyword_set(point) then pt = point+' point'

   #if keyword_set(polygon) then begin
      #pt = 'polygon'
      #args =  [strjoin(strtrim(cx+1,2 )+ ' ' + strtrim(cy+1,2),' ')]
   #endif

   n = len(cx)
   #print args
   #if arg1: args += ','+arg1
   for arg in [arg1, arg2]:
      if arg:
        if hasattr(arg, "__iter__") and not isinstance(arg, str):
           args += (arg,)
           fmt += "%s"
        else:
           fmt += ","+str(arg)

   #if n_elements(arg1) gt 0 then args += ', '+strtrim(arg1+sarg1,2)
   #if n_elements(arg2) gt 0 then args += ', '+strtrim(arg2+sarg2,2)
   #if n_elements(arg3) gt 0 then args += ', '+strtrim(arg3+sarg3,2)

   def optappend(iopt, fmt):
      if iopt:
         if hasattr(iopt, "__iter__") and not isinstance(iopt, str):
            opt.arg += (iopt,)
            opt.fmt += fmt
         else:
            opt.fmt += fmt%iopt

   optappend(size, ' %s')
   optappend(color, ' color=%s')
   optappend(tag1, ' tag={%s}')
   optappend(label, ' text={%s}')
   optappend(optsuf, ' %s')

   if not pt: pt = 'cross point'

   if opt.fmt: opt.fmt = '# ' + opt.fmt

   print(fmt, args+opt.arg)
   lines = [(pt+'('+fmt+')'+opt.fmt)%a for a in zip(*(args+opt.arg))]

   #if n_elements(lines) eq 1 then lines = [lines] ; ensure array

   coord = [coord] if coord else []
   lines = "\n".join(header + coord + lines)

   # check if the port exists
   ports, xpamiss = subprocess.Popen("xpaget xpans | grep 'DS9 "+port+"'", shell=True, stdout=subprocess.PIPE, stderr= subprocess.PIPE, universal_newlines=True, bufsize=0).communicate()

   if ports=='':
      print('xpa misses: ', port)
      return

   #if keyword_set(reset) then $
      #spawn, 'xpaset -p '+port+' frame reset'
   #if keyword_set(frame) then $
      #spawn, 'xpaset -p '+port+' frame '+string(frame)
   if clear: subprocess.call('xpaset -p '+port+' regions delete all', shell=True)

   if not regfile:
   #if ~keyword_set(regfile) then begin
      #; write data directly into bi-directional pipe (race between stdin and stdout)
      #spawn, "xpaset "+port+" regions 2> /dev/null", unit=ounit ; '2> /dev/null' closes stdout?
      #wait, 0.01  ; somehow needed, due to buffering?
      #printf, ounit, transpose(lines)
      #; wait, 0.01  ; somehow needed, due to buffering?
      #; flush, ounit ; does this helps ?
      #free_lun, ounit
      print(lines)
      pipeds9 = subprocess.Popen(['xpaset '+port+' regions'], shell=True, stdin=subprocess.PIPE, universal_newlines=True, bufsize=0)  # This line is needed for python3! Unbuffered and to pass str )
      pipeds9.communicate(lines)
   else:
      print(lines)
      pass

   #endif else if regfile eq '-' then $
      #; may result in % SPAWN: Error managing child process.
      #; Argument list too long
      #;spawn, 'echo -e "'+strjoin(lines,"\n")+'" | xpaset '+port+' regions' $
      #print, transpose(lines) $
   #else begin
      #openw, ounit, regfile, /get_lun
      #printf, ounit, transpose(lines)
      #free_lun, ounit
   #endelse




   #pro ODS9, cx, cy, arg1, arg2, arg3, PORT=port, FRAME=frame, LASTFRAME=lastframe, RESET=reset, LABEL=label, TAG1=tag1, TAG2=tag2, REGFILE=regfile, COLOR=color, PT=pt, BOX=box, CIRCLE=circle, CURVE=CURVE, LINE=LINE, POINT=point, POLYGON=polygon, x=x, cross=cross, RED=red, BLUE=blue, GREEN=green, CLEAR=clear, header=header

#;+
#; NAME:
#;       ODS9
#;
#; VERSION:
#;       v01 (2016-06-30)
#;
#; PURPOSE:
#;       Overplot data point in ds9 as a region file
#;
#; AUTHOR:
#;       M. Zechmeister
#;
#; CALLING SEQUENCE:
#;       DS9, X, Y
#;
#; INPUT:
#;       Cx -   Data vector
#;       Cy -   Data vector
#;
#; OPTIONAL INPUT KEYWORDS:
#;       arg*   - The meaning depends on the selected style.
#;       port   - A named port for an open pipe (address for xpa)
#;       frame  -  Writes to this frame number
#;       /lastframe - Overwrites the last frame
#;       /clear - Deletes all regions
#;       header - a header for the ds9 region file
#;       regfile - Keyword for data transmission
#;                0    direct (bi-directional) pipe (default, not working for some OS)
#;                '-'  pipe via stdin (echo, not working for long input)
#;                filename
#;       ps     - point size (default: 2.5)
#;       color  - color of the elements (vector possible)
#;       pt     - point type (default: circle)
#;                point x y # point=[circle|box|diamond|cross|x|arrow|boxcircle] [size]
#;       curve  - connects points using lines (similar to polygon but not closed)
#;       box    - x y width height angle (default: width=1, height=1)
#;       circle - x y radius (default: radius=2.5)
#;
#;
#; Ellipse
#; Usage: ellipse x y radius radius angle
#;
#; Box
#; Usage: box x y width height angle
#;
#; Polygon
#; Usage: polygon x1 y1 x2 y2 x3 y3 ...
#;
#; Line
#; Usage: line x1 y1 x2 y2 # line=[0|1] [0|1]
#;
#;
#; EXAMPLES:
#;       Display an array and overplot three points
#;
#;       IDL> ds9, dindgen(10,10)
#;       IDL> ods9, [0,5,2], [0,5,4]
#;
#;       IDL> ods9, [0,5,2], [0,5,4], color=['red','blue', 'blue'], /clear
#;       IDL> ods9, [0,5,2], [0,5,4], /blue, tag1=['','good','bad'] ,/clear
#;       IDL> ods9, [0,5,2], [0,5,4], point='cross', color='yellow', /clear
#;
#;       Print the region file
#;
#;       IDL> ods9, [0,5,2], [0,5,4], color='yellow', point='cross', reg='-', $
#;                 head=['# Region file format: DS9 version 4.0', $
#;                       'global point=cross color=yellow font="helvetica 10 normal" select=1 highlite=1 edit=1 move=1 delete=1 include=1 fixed=0 source', 'image' ] ; (coordinate system)
#;
#; NOTES:
#;    see ds9.pro for requirements (xpa)
#;-

   #on_error, 2

   #if n_params() lt 2 then message, '% ods9: no data to display'

   #args = strtrim(cx+1,2) + ', ' + strtrim(cy+1,2)
   #opt = ''

   #; sarg1=0 means arg1 is of type size/width/length.
   #; sarg1=1 means arg1 is of type position and conversion from IDL-zeros to ds9-one based indexing is done
   #sarg1 = 0
   #sarg2 = 0
   #sarg3 = 0

   #if not keyword_set(port) then port = 'idl'

   #if keyword_set(red) then color = 'red'
   #if keyword_set(blue) then color = 'blue'
   #if keyword_set(green) then color = 'green'

   #if keyword_set(box) then begin
      #pt = 'box'
      #if ~n_elements(arg1) then arg1 = 1
      #if ~n_elements(arg2) then arg2 = arg1
   #endif
   #if keyword_set(circle) then begin
      #pt = 'circle'
      #if ~n_elements(arg1) then arg1 = 2.5
   #endif
   #if keyword_set(curve) then begin
      #pt = 'line'
      #args = args[0:*] + ',' + args[1:*]
   #endif
   #if keyword_set(line) then begin
      #pt = ' line'
      #sarg1 = 1
      #sarg2 = 1
      #if size(line,/tname) eq 'STRING' then opt += 'line='+line
   #endif

   #if keyword_set(cross) then point = 'cross'
   #if keyword_set(x) then point = 'x'
   #if keyword_set(point) then pt = point+' point'

   #if keyword_set(polygon) then begin
      #pt = 'polygon'
      #args =  [strjoin(strtrim(cx+1,2 )+ ' ' + strtrim(cy+1,2),' ')]
   #endif

   #if n_elements(arg1) gt 0 then args += ', '+strtrim(arg1+sarg1,2)
   #if n_elements(arg2) gt 0 then args += ', '+strtrim(arg2+sarg2,2)
   #if n_elements(arg3) gt 0 then args += ', '+strtrim(arg3+sarg3,2)

   #if keyword_set(label) then opt += ' text={'+label+'}'
   #if keyword_set(color) then opt += ' color='+color
   #if keyword_set(tag1) then opt += ' tag={'+tag1+'}'
   #if keyword_set(tag2) then opt += ' tag={'+tag2+'}'
   #;tag2 = ~keyword_set(tag2)? '' : ' tag={'+tag2+'}'
   #if ~keyword_set(pt) then pt = 'cross point'


   #lines = pt+'('+args+') # '+opt
   #if n_elements(lines) eq 1 then lines = [lines] ; ensure array

   #if keyword_set(header) then begin
      #lines = [header, lines]
   #endif

   #; check if the port exists
   #spawn, "xpaget xpans | grep 'DS9 "+port+"'", result, err, EXIT_STATUS=xpamiss

   #if xpamiss gt 0 then begin
      #message, string('xpa misses: ', port), /cont
      #return
   #endif

   #if keyword_set(reset) then $
      #spawn, 'xpaset -p '+port+' frame reset'
   #if keyword_set(frame) then $
      #spawn, 'xpaset -p '+port+' frame '+string(frame)
   #if keyword_set(clear) then $
      #spawn, 'xpaset -p '+port+' regions delete all'

   #if ~keyword_set(regfile) then begin
      #; write data directly into bi-directional pipe (race between stdin and stdout)
      #spawn, "xpaset "+port+" regions 2> /dev/null", unit=ounit ; '2> /dev/null' closes stdout?
      #wait, 0.01  ; somehow needed, due to buffering?
      #printf, ounit, transpose(lines)
      #; wait, 0.01  ; somehow needed, due to buffering?
      #; flush, ounit ; does this helps ?
      #free_lun, ounit
   #endif else if regfile eq '-' then $
      #; may result in % SPAWN: Error managing child process.
      #; Argument list too long
      #;spawn, 'echo -e "'+strjoin(lines,"\n")+'" | xpaset '+port+' regions' $
      #print, transpose(lines) $
   #else begin
      #openw, ounit, regfile, /get_lun
      #printf, ounit, transpose(lines)
      #free_lun, ounit
   #endelse

#end
