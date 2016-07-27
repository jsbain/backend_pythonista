#!python2
# currently only py2 supported due to strange matplotlib C bug
import os,sys,time
sys.path.insert(0,os.curdir)
modules = []


def clear_backend(backend):
	clearlist=('matplotlib',
					'pylab',
					'backend',
					'overlay')
	
	for module in sys.modules:
	    if module.startswith(clearlist):
	        modules.append(module)
	for module in modules:
		try:
			sys.modules.pop(module)
		except KeyError:
			pass
	import matplotlib
	matplotlib.use(backend)
	import matplotlib.pyplot as plt
	
# for development: clear out matplotlib
if 'matplotlib.pyplot' in sys.modules:
	import matplotlib
	try:
		if matplotlib.mtime<os.path.getmtime('backend_pythonista.py') \
		or matplotlib.mtime<os.path.getmtime('overlay.py'):
			print('Please wait, clearing out backend')
			clear_backend('agg') # just to make sure we eliminate any backend references in mpl
			clear_backend('module://backend_pythonista')
	except AttributeError:
		pass
matplotlib.use('module://backend_pythonista')
from pylab import *
matplotlib.mtime=time.time()

import backend_pythonista
logger=backend_pythonista.logger  

#p=profile.Profile()
close('all')
print ('********pylab is ready to use!:*****')
print('**** set your interpreter to 2.7 ****')

t=linspace(0,2*pi)
y=sin(t)
y2=sin(t)**2
#logger.setLevel(10)
plot(t,y,'b--',t,y**2,'r.',markersize=2)
title('some plots')
xlabel('\theta')
ylabel('Y')
figure(2)
plot(t,y/t,'k-.')
#p.create_stats()


