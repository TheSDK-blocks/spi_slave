import os
import sys
if not (os.path.abspath('../../thesdk') in sys.path):
    sys.path.append(os.path.abspath('../../thesdk'))

import numpy as np

from thesdk import *
from rtl import *
from rtl.testbench import *
#from rtl.entity import *
from rtl.testbench import testbench as vtb

class spi_slave(rtl,thesdk):
    @property
    def _classfile(self):
        return os.path.dirname(os.path.realpath(__file__)) + "/"+__name__

    def __init__(self,*arg): 
        self.print_log(type='I', msg='Inititalizing %s' %(__name__)) 
        self.proplist = [ 'Rs' ];    # Properties that can be propagated from parent
        self.Rs =  100e6;            # Sampling frequency
        self.IOS=Bundle()
        self.IOS.Members['monitor_in']=IO() # Pointer for input data
        _=rtl_iofile(self,name='monitor_in', dir='in', iotype='sample', ionames=['io_monitor_in'])
        self.IOS.Members['config_out']=IO() # Pointer for input data
        _=rtl_iofile(self,name='config_out', dir='out', iotype='sample', ionames=['io_config_out'])
        self.IOS.Members['miso']=IO()       # Pointer for input data
        _=rtl_iofile(self,name='miso', dir='out', iotype='sample', ionames=['io_miso'])
        
        self.model='py';             # Can be set externally, but is not propagated
        self.par= False              # By default, no parallel processing
        self.queue= []               # By default, no parallel processing
        #Collects mosi, cs and sclk controlled by master
        self.IOS.Members['control_write']= IO() 
        #This is a placeholder, file is created by controller
        #_=rtl_iofile(self,name='control_write', dir='in', iotype='event', ionames=['reset', 'initdone', 'io_cs', 'io_mosi', 'io_sclk'])
        
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
        pass

    def run(self,*arg):
        if len(arg)>0:
            self.par=True      #flag for parallel processing
            self.queue=arg[0]  #multiprocessing.queue as the first argument
        if self.model=='py':
            self.main()
        else: 
          if self.model=='sv':
              self.vlogmodulefiles=list(['async_set_register.v'])
              self.rtlparameters=dict([ ('g_Rs',self.Rs),]) #Defines the sample rate

          elif self.model=='vhdl':
              self.vhdlentityfiles=list(['synchronizer_n.vhd'])
              self.rtlparameters=dict(
                      [ ('g_Rs',self.Rs), ('g_size_config',4), ('g_size_monitor',4), 
                          ('g_mode_select',1)]
                  ) 
          self.run_rtl()
          del self.iofile_bundle #Large files should be deletedl
          self.IOS.Members['miso'].Data=self.IOS.Members['miso'].Data.astype('int')

    def define_io_conditions(self):
        # Input A is read to verilog simulation after 'initdone' is set to 1 by controller
        self.iofile_bundle.Members['monitor_in'].verilog_io_condition='initdone'
        # Output is read to verilog simulation when all of the utputs are valid, 
        # and after 'initdo' is set to 1 by controller
        self.iofile_bundle.Members['config_out'].verilog_io_condition_append(cond='&& initdone')
        # In Cpol0 Cpha1 miso is read with falling edge of sclk
        self.iofile_bundle.Members['miso'].verilog_io_sync='@(negedge io_sclk)\n'
        self.iofile_bundle.Members['miso'].verilog_io_condition_append(cond='&& initdone')


if __name__=="__main__":
    import matplotlib.pyplot as plt
    from  spi_slave import *
    from  spi_slave.controller import controller as spi_controller
    import pdb
    length=1024
    rs=100e6
    #indata=np.random.randint(2,size=length).reshape(-1,1);
    indata=np.array([5]).reshape(-1,1)
    controller=spi_controller()
    controller.Rs=rs
    controller.reset()
    controller.step_time()
    controller.start_datafeed()
    controller.step_time()
    #Should this be a string or array
    spi_data=[ 
            '10110011', 
            '11000011',
            '00100011'
            ]
    # We expect to get the indata value at the lsb's
    expected=[ 
            '10110101', 
            '11000101',
            '00100101'
            ]

    for data in spi_data:
        controller.write_spi(value=data)
        controller.step_time()
        controller.step_time()


    duts=[spi_slave() for i in range(2) ]
    duts[0].model='sv'
    duts[1].model='vhdl'
    #pdb.set_trace()
    for d in duts: 
        d.Rs=rs
        d.interactive_rtl=False
        d.IOS.Members['monitor_in'].Data=indata
        d.IOS.Members['control_write']=controller.IOS.Members['control_write']
        d.init()
        print( "\nVerifying %s implementation.\n" %(d.model))
        d.run()
        #print('Vector received is \n%s' %(d.IOS.Members['miso'].Data))
        received=d.IOS.Members['miso'].Data[::-1]
        received=np.flipud(received[0:int(received.shape[0]/8)*8].reshape(-1,8))

        for i in range(received.shape[0]):
            rstr=''.join(map(str,received[i,:]))
            fail=False
            if rstr==expected[i]:
                print("Received string %s matches with string %s expected." %(rstr,expected[i]))
            else:
                print("%sth Received string %s DOES NOT MATCH with string %s expected."
                        %(i,rstr,expected[i]))
                fail=True
        if fail:
            print( "Your %s implementation sucks like Electrolux!" %(d.model))
        else:
            print( "Your %s implementation is OK" %(d.model))
