import os
import sys
if not (os.path.abspath('../../thesdk') in sys.path):
    sys.path.append(os.path.abspath('../../thesdk'))

import numpy as np

from thesdk import *
from vhdl import *
from vhdl.testbench import *
from vhdl.entity import *
from vhdl.testbench import testbench as vtb

class spi_slave(vhdl,thesdk):
    @property
    def _classfile(self):
        return os.path.dirname(os.path.realpath(__file__)) + "/"+__name__

    def __init__(self,*arg): 
        self.print_log(type='I', msg='Inititalizing %s' %(__name__)) 
        self.proplist = [ 'Rs' ];    # Properties that can be propagated from parent
        self.Rs =  100e6;            # Sampling frequency
        self.IOS=Bundle()
        self.IOS.Members['A']=IO() # Pointer for input data
        #_=verilog_iofile(self,name='A', dir='in', iotype='sample', ionames=['A']) # IO file for input A
        
        self.IOS.Members['Z']= IO()
        #_= vhdl_iofile(self,name='Z', dir='out', iotype='sample', ionames=['Z'], datatype='int')
        self.model='py';             # Can be set externally, but is not propagated
        self.par= False              # By default, no parallel processing
        self.queue= []               # By default, no parallel processing
        self.IOS.Members['control_write']= IO() 
        # This is a placeholder, file is created elsewher
        #_=verilog_iofile(self, name='control_write', dir='in', iotype='file') 
        
        if len(arg)>=1:
            parent=arg[0]
            self.copy_propval(parent,self.proplist)
            self.parent =parent;

        self.init()

    def init(self):
        pass
        ### Lets fix this later on
        #if self.model=='vhdl':
        #    self.print_log(type='F', msg='VHDL simulation is not supported with v1.2\n Use v1.1')

    def main(self):
        out=np.array(1-self.IOS.Members['A'].Data)
        if self.par:
            self.queue.put(out)
        self.IOS.Members['Z'].Data=out

    def run(self,*arg):
        if len(arg)>0:
            self.par=True      #flag for parallel processing
            self.queue=arg[0]  #multiprocessing.queue as the first argument
        if self.model=='py':
            self.main()
        else: 
          if self.model=='sv':
             self.print_log(type='F', msg='Verilog simulation is not supported')
          elif self.model=='vhdl':
              self.vhdlparameters=dict([ ('g_Rs',self.Rs),]) #Defines the sample rate
              self.dut=vhdl_entity(file=self.entitypath+'/vhdl/'+'spi_slave.vhd')
              if self.par:
                 self.queue.put(self.IOS.Members[Z].Data)
              del self.iofile_bundle #Large files should be deletedl


    #def define_io_conditions(self):
    #    # Input A is read to verilog simulation after 'initdo' is set to 1 by controller
    #    self.iofile_bundle.Members['A'].verilog_io_condition='initdone'
    #    # Output is read to verilog simulation when all of the utputs are valid, 
    #    # and after 'initdo' is set to 1 by controller
    #    self.iofile_bundle.Members['Z'].verilog_io_condition_append(cond='&& initdone')


if __name__=="__main__":
    import matplotlib.pyplot as plt
    from  spi_slave import *
    #from  spi_slave.controller import controller as spi_controller
    import pdb
    length=1024
    rs=100e6
    #indata=np.random.randint(2,size=length).reshape(-1,1);
    #controller=spi_controller()
    #controller.Rs=rs
    #controller.reset()
    #controller.step_time()
    #controller.start_datafeed()

    dut=spi_slave()
    dut.model='vhdl'
    dut.run()
    print(dut.dut.definition)
#    pdb.set_trace()


    #duts=[spi_slave() for i in range(2) ]
    #duts[0].model='py'
    #duts[1].model='vhdl'
    #for d in duts: 
    #    d.Rs=rs
    #    #d.interactive_verilog=True
    #    d.IOS.Members['A'].Data=indata
    #    #d.IOS.Members['control_write']=controller.IOS.Members['control_write']
    #    #d.init()
    #    #d.run()

    # Obs the latencies may be different
    #latency=[ 0 , 1 ]
    #for k in range(len(duts)):
    #    figure=plt.figure()
    #    h=plt.subplot();
    #    hfont = {'fontname':'Sans'}
    #    x = np.linspace(0,10,11).reshape(-1,1)
    #    markerline, stemlines, baseline = plt.stem(\
    #            x,indata[0:11,0],'-.'
    #        )
    #    markerline, stemlines, baseline = plt.stem(\
    #            x, duts[k].IOS.Members['Z'].Data[0+latency[k]:11+latency[k],0], '-.'
    #        )
    #    plt.setp(markerline,'markerfacecolor', 'b','linewidth',2)
    #    plt.setp(stemlines, 'linestyle','solid','color','b', 'linewidth', 2)
    #    plt.ylim(0, 1.1);
    #    plt.xlim((np.amin(x), np.amax(x)));
    #    str = "Inverter model %s" %(duts[k].model) 
    #    plt.suptitle(str,fontsize=20);
    #    plt.ylabel('Out', **hfont,fontsize=18);
    #    plt.xlabel('Sample (n)', **hfont,fontsize=18);
    #    h.tick_params(labelsize=14)
    #    plt.grid(True);
    #    printstr="./inv_%s.eps" %(duts[k].model)
    #    plt.show(block=False);
    #    figure.savefig(printstr, format='eps', dpi=300);
    input()
