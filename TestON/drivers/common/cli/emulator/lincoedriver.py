#!/usr/bin/env python

"""
This driver handles the optical switch emulator linc-oe.

Please follow the coding style demonstrated by existing
functions and document properly.

If you are a contributor to the driver, please
list your email here for future contact:

    andrew@onlab.us
    shreya@onlab.us

OCT 20 2014
"""
import traceback
import pexpect
import struct
import fcntl
import os
import signal
import re
import sys
import core.teston
import time
sys.path.append( "../" )
from math import pow
from drivers.common.cli.emulatordriver import Emulator
from drivers.common.clidriver import CLI


class LincOEDriver( Emulator ):

    """
    LincOEDriver class will handle all emulator functions
    """
    def __init__( self ):
        super( Emulator, self ).__init__()
        self.handle = self
        self.wrapped = sys.modules[ __name__ ]
        self.flag = 0

    def connect( self, **connectargs ):
        """
        Create ssh handle for Linc-OE cli
        """
        import time

        for key in connectargs:
            vars( self )[ key ] = connectargs[ key ]

        self.name = self.options[ 'name' ]
        self.handle = \
            super( LincOEDriver, self ).connect(
                user_name=self.user_name,
                ip_address=self.ip_address,
                port=None,
                pwd=self.pwd )

        self.sshHandle = self.handle

        if self.handle:
            main.log.info( "Handle successfully created" )
            self.home = "~/linc-oe"

            self.handle.sendline( "cd " + self.home )
            self.handle.expect( "oe$" )

            print "handle = ", self.handle.before

            return main.TRUE
        else:
            main.log.error( self.name +
                            ": Connection failed to the host " +
                            self.user_name + "@" + self.ip_address )
            main.log.error( self.name +
                            ": Failed to connect to Linc-OE" )
            return main.FALSE

    def startConsole( self ):
        import time
        main.log.info(
            self.name +
            ": Starting Linc-OE CLI.. This may take a while" )
        time.sleep( 30 )
        self.handle.sendline( "sudo ./rel/linc/bin/linc console" )
        j = self.handle.expect( [ "linc@", pexpect.EOF, pexpect.TIMEOUT ] )
        startResult = self.handle.before
        if j == 0:
            main.log.info( "Linc-OE CLI started" )
            return main.TRUE
        else:
            main.log.error(
                self.name +
                ": Connection failed to the host " +
                self.user_name +
                "@" +
                self.ip_address )
            main.log.error( self.name +
                            ": Failed to connect to Linc-OE" )
            return main.FALSE

    def build( self ):
        """
        Build Linc-OE with the specified settings
        """
        try:
            self.handle.sendline( "make rel" )
            i = self.handle.expect( [
                "ERROR",
                "\$" ] )

            if i == 0:
                self.handle.sendline( "sudo pkill -9 epmd" )
                self.handle.sendline( "make rel" )
                self.handle.expect( "\$" )

                handle = self.handle.before
                return handle

            else:
                return main.TRUE

        except pexpect.EOF:
            main.log.error( self.name + ": EOF exception" )
            main.log.error( self.name + ":    " + self.handle.before )
            main.cleanup()
            main.exit()
        except:
            main.log.info( self.name + " :::::::" )
            main.log.error( traceback.print_exc() )
            main.log.info( self.name + " :::::::" )
            main.cleanup()
            main.exit()

    def setInterfaceUp( self, intfs ):
        """
        Specify interface to bring up.
        When Linc-OE is started, tap interfaces should
        be created. They must be brought up manually
        """
        try:
            self.handle.sendline( "ifconfig " + str( intfs ) + " up" )
            self.handle.expect( "linc@" )

            handle = self.handle.before

            return handle

        except pexpect.EOF:
            main.log.error( self.name + ": EOF exception" )
            main.log.error( self.name + ":    " + self.handle.before )
            main.cleanup()
            main.exit()
        except:
            main.log.info( self.name + " :::::::" )
            main.log.error( traceback.print_exc() )
            main.log.info( self.name + " :::::::" )
            main.cleanup()
            main.exit()

    def startSwitch( self, swId ):
        """
        Start a logical switch using switch id
        """
        try:
            self.handle.sendline( "linc:start_switch(" + str( swId ) + ")." )
            self.handle.expect( "linc@" )

            handle = self.handle.before

        except pexpect.EOF:
            main.log.error( self.name + ": EOF exception" )
            main.log.error( self.name + ":    " + self.handle.before )
            main.cleanup()
            main.exit()
        except:
            main.log.info( self.name + " :::::::" )
            main.log.error( traceback.print_exc() )
            main.log.info( self.name + " :::::::" )
            main.cleanup()
            main.exit()

    def stopSwitch( self, swId ):
        """
        Stop a logical switch using switch id
        """
        try:
            self.handle.sendline( "linc:stop_switch(" + str( swId ) + ")." )
            self.handle.expect( "linc@" )

            handle = self.handle.before

        except pexpect.EOF:
            main.log.error( self.name + ": EOF exception" )
            main.log.error( self.name + ":    " + self.handle.before )
            main.cleanup()
            main.exit()
        except:
            main.log.info( self.name + " :::::::" )
            main.log.error( traceback.print_exc() )
            main.log.info( self.name + " :::::::" )
            main.cleanup()
            main.exit()

    def getDatapathId( self, swId ):
        """
        Get datapath id of a specific switch by switch id
        """
        try:
            self.handle.sendline( "linc_logic:get_datapath_id(" +
                                  str( swId ) + ")." )
            self.handle.expect( "linc@" )

            handle = self.handle.before

        except pexpect.EOF:
            main.log.error( self.name + ": EOF exception" )
            main.log.error( self.name + ":    " + self.handle.before )
            main.cleanup()
            main.exit()
        except:
            main.log.info( self.name + " :::::::" )
            main.log.error( traceback.print_exc() )
            main.log.info( self.name + " :::::::" )
            main.cleanup()
            main.exit()

    def listPorts( self, swId ):
        """
        List all ports of a switch by switch id
        """
        try:
            self.handle.sendline( "linc:ports(" + str( swId ) + ")." )
            self.handle.expect( "linc@" )

            handle = self.handle.before

        except pexpect.EOF:
            main.log.error( self.name + ": EOF exception" )
            main.log.error( self.name + ":    " + self.handle.before )
            main.cleanup()
            main.exit()
        except:
            main.log.info( self.name + " :::::::" )
            main.log.error( traceback.print_exc() )
            main.log.info( self.name + " :::::::" )
            main.cleanup()
            main.exit()

    def portUp( self, swId, ptId ):
        """
        Bring port up using switch id and port id
        """
        try:
            self.handle.sendline( "linc:port_up(" +
                                  str( swId ) + ", " + str( ptId ) + ")." )
            self.handle.expect( "linc@" )

            handle = self.handle.before

        except pexpect.EOF:
            main.log.error( self.name + ": EOF exception" )
            main.log.error( self.name + ":    " + self.handle.before )
            main.cleanup()
            main.exit()
        except:
            main.log.info( self.name + " :::::::" )
            main.log.error( traceback.print_exc() )
            main.log.info( self.name + " :::::::" )
            main.cleanup()
            main.exit()

    def portDown( self, swId, ptId ):
        """
        Bring port down using switch id and port id
        """
        try:
            self.handle.sendline( "linc:port_down(" +
                                  str( swId ) + ", " + str( ptId ) + ")." )
            self.handle.expect( "linc@" )

            handle = self.handle.before

        except pexpect.EOF:
            main.log.error( self.name + ": EOF exception" )
            main.log.error( self.name + ":    " + self.handle.before )
            main.cleanup()
            main.exit()
        except:
            main.log.info( self.name + " :::::::" )
            main.log.error( traceback.print_exc() )
            main.log.info( self.name + " :::::::" )
            main.cleanup()
            main.exit()

    def stopLincOEConsole( self ):
        """
        This function is only used for packet optical testing
        Send disconnect prompt to Linc-OE CLI
        ( CTRL+C ) and kill the linc process
        """
        try:
            cmd = "pgrep -f linc"
            self.handle.sendline( "pgrep -f linc" )
            self.handle.expect( "linc" )
            print "stophandle = ", self.handle.before
        except pexpect.EOF:
            main.log.error( self.name + ": EOF exception" )
            main.log.error( self.name + ":    " + self.handle.before )

    def disconnect( self ):
        """
        Send disconnect prompt to Linc-OE CLI
        ( CTRL+C ) and kill the linc process
        """
        try:
            # Send CTRL+C twice to exit CLI
            self.handle.send( "\x03" )
            self.handle.send( "\x03" )
            self.handle.expect( "\$" )
            handle1 = self.handle.before
            cmd = "pgrep -f linc"
            self.handle.sendline( cmd )
            self.handle.expect( "\$" )
            handle2 = self.handle.before
            main.log.info( "pid's = " + handle2 )
            cmd = "sudo kill -9 `pgrep -f linc`"
            self.handle.sendline( cmd )
            self.handle.expect( "\$" )

        except pexpect.EOF:
            main.log.error( self.name + ": EOF exception" )
            main.log.error( self.name + ":    " + self.handle.before )
            main.cleanup()
            main.exit()
        except:
            main.log.info( self.name + " :::::::" )
            main.log.error( traceback.print_exc() )
            main.log.info( self.name + " :::::::" )
            main.cleanup()
            main.exit()

if __name__ != "__main__":
    import sys
    sys.modules[ __name__ ] = LincOEDriver()
