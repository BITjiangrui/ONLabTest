# TopoPerfNext
#
# Topology Convergence scale-out test for ONOS-next
# NOTE: This test supports up to 7 nodes scale-out scenario
#
# NOTE: Ensure that you have 'tablet.json' file
#      in the onos/tools/package/config directory
# NOTE: You must start this test initially with 3 nodes
#
# andrew@onlab.us

import time
import sys
import os
import re


class TopoConvNext:

    def __init__( self ):
        self.default = ''

    def CASE1( self, main ):
        """
        ONOS startup sequence
        """
        import time

        #******
        # Global cluster count for scale-out purposes
        global cluster_count
        global topo_iteration
        topo_iteration = 1
        cluster_count = 1
        #******
        cell_name = main.params[ 'ENV' ][ 'cellName' ]

        git_pull = main.params[ 'GIT' ][ 'autoPull' ]
        checkout_branch = main.params[ 'GIT' ][ 'checkout' ]

        ONOS1_ip = main.params[ 'CTRL' ][ 'ip1' ]
        ONOS2_ip = main.params[ 'CTRL' ][ 'ip2' ]
        ONOS3_ip = main.params[ 'CTRL' ][ 'ip3' ]
        ONOS4_ip = main.params[ 'CTRL' ][ 'ip4' ]
        ONOS5_ip = main.params[ 'CTRL' ][ 'ip5' ]
        ONOS6_ip = main.params[ 'CTRL' ][ 'ip6' ]
        ONOS7_ip = main.params[ 'CTRL' ][ 'ip7' ]
        MN1_ip = main.params[ 'MN' ][ 'ip1' ]
        BENCH_ip = main.params[ 'BENCH' ][ 'ip' ]

        main.case( "Setting up test environment" )
        main.log.info( "copying topology event accumulator config file" +
                       " to ONOS package/etc/ directory" )
        topo_config_name = main.params[ 'TEST' ][ 'topo_config_name' ]
        topo_config =\
            main.params[ 'TEST' ][ 'topo_accumulator_config' ]
        main.ONOSbench.handle.sendline( "cp ~/" + topo_config +
                                        " ~/ONOS/tools/package/etc/" +
                                        topo_config_name )
        main.ONOSbench.handle.expect( "\$" )

        main.log.info( "Uninstalling previous instances" )
        #main.ONOSbench.onos_uninstall( node_ip=ONOS1_ip )
        main.ONOSbench.onos_uninstall( node_ip=ONOS2_ip )
        main.ONOSbench.onos_uninstall( node_ip=ONOS3_ip )
        main.ONOSbench.onos_uninstall( node_ip=ONOS4_ip )
        main.ONOSbench.onos_uninstall( node_ip=ONOS5_ip )
        main.ONOSbench.onos_uninstall( node_ip=ONOS6_ip )
        main.ONOSbench.onos_uninstall( node_ip=ONOS7_ip )

        main.log.report( "Setting up test environment" )

        main.step( "Creating cell file" )
        cell_file_result = main.ONOSbench.create_cell_file(
            BENCH_ip, cell_name, MN1_ip,
            "onos-core,onos-app-metrics",
            # ONOS1_ip, ONOS2_ip, ONOS3_ip )
            ONOS1_ip )

        main.step( "Applying cell file to environment" )
        cell_apply_result = main.ONOSbench.set_cell( cell_name )
        verify_cell_result = main.ONOSbench.verify_cell()

        main.step( "Removing raft logs" )
        main.ONOSbench.onos_remove_raft_logs()
        time.sleep( 10 )

        main.step( "Git checkout and pull " + checkout_branch )
        if git_pull == 'on':
            checkout_result = \
                main.ONOSbench.git_checkout( checkout_branch )
            pull_result = main.ONOSbench.git_pull()
        else:
            checkout_result = main.TRUE
            pull_result = main.TRUE
            main.log.info( "Skipped git checkout and pull" )

        main.log.report( "Commit information - " )
        main.ONOSbench.get_version()

        main.step( "Using mvn clean & install" )
        #mvn_result = main.ONOSbench.clean_install()
        mvn_result = main.TRUE

        main.step( "Set cell for ONOS cli env" )
        main.ONOS1cli.set_cell( cell_name )
        # main.ONOS2cli.set_cell( cell_name )
        # main.ONOS3cli.set_cell( cell_name )

        main.step( "Creating ONOS package" )
        package_result = main.ONOSbench.onos_package()

        # Start test with single node only
        main.step( "Installing ONOS package" )
        install1_result = main.ONOSbench.onos_install( node=ONOS1_ip )
        #install2_result = main.ONOSbench.onos_install( node=ONOS2_ip )
        #install3_result = main.ONOSbench.onos_install( node=ONOS3_ip )

        time.sleep( 10 )

        main.step( "Start onos cli" )
        cli1 = main.ONOS1cli.start_onos_cli( ONOS1_ip )
        #cli2 = main.ONOS2cli.start_onos_cli( ONOS2_ip )
        #cli3 = main.ONOS3cli.start_onos_cli( ONOS3_ip )

        main.step( "Enable metrics feature" )
        # main.ONOS1cli.feature_install( "onos-app-metrics" )

        utilities.assert_equals( expect=main.TRUE,
                                 actual=cell_file_result and cell_apply_result and
                                 verify_cell_result and checkout_result and
                                 pull_result and mvn_result and
                                 install1_result,  # and install2_result and
                                 # install3_result,
                                 onpass="Test Environment setup successful",
                                 onfail="Failed to setup test environment" )

    def CASE2( self, main ):
        """
        100 Switch discovery latency

        Important:
            This test case can be potentially dangerous if
            your machine has previously set iptables rules.
            One of the steps of the test case will flush
            all existing iptables rules.
        Note:
            You can specify the number of switches in the
            params file to adjust the switch discovery size
            ( and specify the corresponding topology in Mininet1
            .topo file )
        """
        import time
        import subprocess
        import os
        import requests
        import json
        import numpy

        ONOS_ip_list = []
        ONOS_ip_list.append( '0' )
        ONOS_ip_list.append( main.params[ 'CTRL' ][ 'ip1' ] )
        ONOS_ip_list.append( main.params[ 'CTRL' ][ 'ip2' ] )
        ONOS_ip_list.append( main.params[ 'CTRL' ][ 'ip3' ] )
        ONOS_ip_list.append( main.params[ 'CTRL' ][ 'ip4' ] )
        ONOS_ip_list.append( main.params[ 'CTRL' ][ 'ip5' ] )
        ONOS_ip_list.append( main.params[ 'CTRL' ][ 'ip6' ] )
        ONOS_ip_list.append( main.params[ 'CTRL' ][ 'ip7' ] )
        MN1_ip = main.params[ 'MN' ][ 'ip1' ]
        ONOS_user = main.params[ 'CTRL' ][ 'user' ]

        default_sw_port = main.params[ 'CTRL' ][ 'port1' ]

        # Number of iterations of case
        num_iter = main.params[ 'TEST' ][ 'numIter' ]
        iter_ignore = int( main.params[ 'TEST' ][ 'iterIgnore' ] )

        #***********
        # Global number of switches that change
        # throughout the test
        global num_sw
        global topo_iteration
        global cluster_count
        if topo_iteration == 1:
            num_sw = main.params[ 'TEST' ][ 'numSwitch1' ]
        elif topo_iteration == 2:
            num_sw = main.params[ 'TEST' ][ 'numSwitch2' ]
        elif topo_iteration == 3:
            num_sw = main.params[ 'TEST' ][ 'numSwitch3' ]
        elif topo_iteration == 4:
            num_sw = main.params[ 'TEST' ][ 'numSwitch4' ]
        #***********

        # Timestamp 'keys' for json metrics output.
        # These are subject to change, hence moved into params
        deviceTimestamp = main.params[ 'JSON' ][ 'deviceTimestamp' ]
        graphTimestamp = main.params[ 'JSON' ][ 'graphTimestamp' ]

        # Threshold for this test case
        sw_disc_threshold_str = main.params[ 'TEST' ][ 'swDisc100Threshold' ]
        sw_disc_threshold_obj = sw_disc_threshold_str.split( "," )
        sw_disc_threshold_min = int( sw_disc_threshold_obj[ 0 ] )
        sw_disc_threshold_max = int( sw_disc_threshold_obj[ 1 ] )

        assertion = main.TRUE
        sw_discovery_lat_list = []
        syn_ack_delta_list = []

        main.case( str( num_sw ) + " switches distributed across " +
                   str( cluster_count ) + " nodes convergence latency" )

        main.log.report( "Large topology convergence and scale-out test" )
        main.log.report( "Currently active ONOS node(s): " )
        report_str = "Node "
        for node in range( 1, cluster_count + 1 ):
            report_str += ( str( node ) + " " )
        main.log.report( report_str )
        main.log.report( "Topology size: " + str( num_sw ) + " switches" )

        main.step( "Distributing " + num_sw + " switches to each ONOS" )
        index = 1
        for node in range( 1, cluster_count + 1 ):
            for i in range( index, ( int( num_sw ) / cluster_count ) + index ):
                main.Mininet1.assign_sw_controller(
                    sw=str( i ),
                    ip1=ONOS_ip_list[ node ],
                    port1=default_sw_port )
            index = i + 1
        # for i in range( 1, int( num_sw )+1 ):
            # main.Mininet1.assign_sw_controller(
            # sw=str( i ),
            # ip1="10.128.174.1",
            #            port1="6633" )

        main.log.info( "Please check ptpd configuration to ensure " +
                       "all nodes' system times are in sync" )

        time.sleep( 10 )

        for i in range( 0, int( num_iter ) ):
            main.step( "Set iptables rule to block sw connections" )

            # INPUT rules
            main.ONOS1.handle.sendline(
                "sudo iptables -A INPUT -p tcp -s " +
                MN1_ip + " --dport " + default_sw_port + " -j DROP" )
            main.ONOS2.handle.sendline(
                "sudo iptables -A INPUT -p tcp -s " +
                MN1_ip + " --dport " + default_sw_port + " -j DROP" )
            main.ONOS3.handle.sendline(
                "sudo iptables -A INPUT -p tcp -s " +
                MN1_ip + " --dport " + default_sw_port + " -j DROP" )
            main.ONOS4.handle.sendline(
                "sudo iptables -A INPUT -p tcp -s " +
                MN1_ip + " --dport " + default_sw_port + " -j DROP" )
            main.ONOS5.handle.sendline(
                "sudo iptables -A INPUT -p tcp -s " +
                MN1_ip + " --dport " + default_sw_port + " -j DROP" )
            main.ONOS6.handle.sendline(
                "sudo iptables -A INPUT -p tcp -s " +
                MN1_ip + " --dport " + default_sw_port + " -j DROP" )
            main.ONOS7.handle.sendline(
                "sudo iptables -A INPUT -p tcp -s " +
                MN1_ip + " --dport " + default_sw_port + " -j DROP" )

            # OUTPUT rules
            main.ONOS1.handle.sendline(
                "sudo iptables -A OUTPUT -p tcp -s " +
                MN1_ip + " --dport " + default_sw_port + " -j DROP" )
            main.ONOS2.handle.sendline(
                "sudo iptables -A OUTPUT -p tcp -s " +
                MN1_ip + " --dport " + default_sw_port + " -j DROP" )
            main.ONOS3.handle.sendline(
                "sudo iptables -A OUTPUT -p tcp -s " +
                MN1_ip + " --dport " + default_sw_port + " -j DROP" )
            main.ONOS4.handle.sendline(
                "sudo iptables -A OUTPUT -p tcp -s " +
                MN1_ip + " --dport " + default_sw_port + " -j DROP" )
            main.ONOS5.handle.sendline(
                "sudo iptables -A OUTPUT -p tcp -s " +
                MN1_ip + " --dport " + default_sw_port + " -j DROP" )
            main.ONOS6.handle.sendline(
                "sudo iptables -A OUTPUT -p tcp -s " +
                MN1_ip + " --dport " + default_sw_port + " -j DROP" )
            main.ONOS7.handle.sendline(
                "sudo iptables -A OUTPUT -p tcp -s " +
                MN1_ip + " --dport " + default_sw_port + " -j DROP" )

            main.log.info( "Please wait for switch connection to timeout" )

            # time.sleep( 60 )
            # if cluster_count >= 3:
            #    time.sleep( 60 )
            # if cluster_count >= 5:
            #    time.sleep( 30 )
            # if cluster_count >= 6:
            #    time.sleep( 30 )

            if cluster_count >= 3:
                main.ONOS1.handle.sendline(
                    "tshark -i eth0 -t e | " +
                    "grep 'SYN, ACK' | grep '6633' >" +
                    "/tmp/syn_ack_onos1_iter" +
                    str( i ) +
                    ".txt &" )
                main.ONOS2.handle.sendline(
                    "tshark -i eth0 -t e | " +
                    "grep 'SYN, ACK' | grep '6633' >" +
                    "/tmp/syn_ack_onos2_iter" +
                    str( i ) +
                    ".txt &" )
                main.ONOS3.handle.sendline(
                    "tshark -i eth0 -t e | " +
                    "grep 'SYN, ACK' | grep '6633' >" +
                    "/tmp/syn_ack_onos3_iter" +
                    str( i ) +
                    ".txt &" )
            if cluster_count >= 4:
                main.ONOS4.handle.sendline(
                    "tshark -i eth0 -t e | " +
                    "grep 'SYN, ACK' | grep '6633' >" +
                    "/tmp/syn_ack_onos4_iter" +
                    str( i ) +
                    ".txt &" )
            if cluster_count >= 5:
                main.ONOS5.handle.sendline(
                    "tshark -i eth0 -t e | " +
                    "grep 'SYN, ACK' | grep '6633' >" +
                    "/tmp/syn_ack_onos5_iter" +
                    str( i ) +
                    ".txt &" )
            if cluster_count >= 6:
                main.ONOS6.handle.sendline(
                    "tshark -i eth0 -t e | " +
                    "grep 'SYN, ACK' | grep '6633' >" +
                    "/tmp/syn_ack_onos6_iter" +
                    str( i ) +
                    ".txt &" )
            if cluster_count == 7:
                main.ONOS7.handle.sendline(
                    "tshark -i eth0 -t e | " +
                    "grep 'SYN, ACK' | grep '6633' >" +
                    "/tmp/syn_ack_onos6_iter" +
                    str( i ) +
                    ".txt &" )

            # NOTE:
            #       Delay before checking devices to
            #       help prevent timing out from CLI
            #       due to multiple command issuing
            time.sleep( 20 )

            loop = True
            loop_count = 0
            device_count = 0
            while loop_count < 60 and loop:
                main.log.info( "Checking devices for device down" )

                temp_len = 0
                device_str1 = main.ONOS1cli.devices(
                    node_ip=ONOS_ip_list[ 1 ] )
                device_json1 = json.loads( device_str1 )
                json_len = len( device_json1 )

                # NOTE: May want to check the rest of
                #      the ONOS instances for device down as well

                for device1 in device_json1:
                    temp_len = temp_len + 1
                    if device1[ 'available' ]:
                        loop = True
                        break
                    # if I'm on the last json object and I still haven't
                    # broken out of the loop, it means there were
                    # no available devices
                    elif temp_len == json_len - 1:
                        main.log.info( "Temp length: " + str( temp_len ) )
                        main.step( "Flushing iptables and obtaining t0" )
                        t0_system = time.time() * 1000

                        main.ONOS1.handle.sendline( "sudo iptables -F" )
                        main.ONOS2.handle.sendline( "sudo iptables -F" )
                        main.ONOS3.handle.sendline( "sudo iptables -F" )
                        main.ONOS4.handle.sendline( "sudo iptables -F" )
                        main.ONOS5.handle.sendline( "sudo iptables -F" )
                        main.ONOS6.handle.sendline( "sudo iptables -F" )
                        main.ONOS7.handle.sendline( "sudo iptables -F" )

                        loop = False
                        break

                loop_count += 1
                time.sleep( 1 )

            main.log.info( "System time t0: " + str( t0_system ) )

            counter_loop = 0
            counter_avail1 = 0
            counter_avail2 = 0
            counter_avail3 = 0
            counter_avail4 = 0
            counter_avail5 = 0
            counter_avail6 = 0
            counter_avail7 = 0
            onos1_dev = False
            onos2_dev = False
            onos3_dev = False
            onos4_dev = False
            onos5_dev = False
            onos6_dev = False
            onos7_dev = False

            # TODO: Think of a more elegant way to check all
            #      switches across all nodes
            # Goodluck debugging this loop
            while counter_loop < 60:
                for node in range( 1, cluster_count + 1 ):
                    if node == 1 and not onos1_dev:
                        main.log.info( "Checking node 1 for device " +
                                       "discovery" )
                        device_str_obj1 = main.ONOS1cli.devices(
                            node_ip=ONOS_ip_list[ 1 ] )
                        device_json1 = json.loads( device_str_obj1 )
                        for device1 in device_json1:
                            if device1[ 'available' ]:
                                counter_avail1 += 1
                                if counter_avail1 == int( num_sw ):
                                    onos1_dev = True
                                    main.log.info( "All devices have been" +
                                                   " discovered on ONOS1" )
                            else:
                                counter_avail1 = 0
                    if node == 2 and not onos2_dev:
                        main.log.info( "Checking node 2 for device " +
                                       "discovery" )
                        device_str_obj2 = main.ONOS2cli.devices(
                            node_ip=ONOS_ip_list[ 2 ] )
                        device_json2 = json.loads( device_str_obj2 )
                        for device2 in device_json2:
                            if device2[ 'available' ]:
                                counter_avail2 += 1
                                if counter_avail2 == int( num_sw ):
                                    onos2_dev = True
                                    main.log.info( "All devices have been" +
                                                   " discovered on ONOS2" )
                            else:
                                counter_avail2 = 0
                    if node == 3 and not onos3_dev:
                        main.log.info( "Checking node 3 for device " +
                                       "discovery" )
                        device_str_obj3 = main.ONOS3cli.devices(
                            node_ip=ONOS_ip_list[ 3 ] )
                        device_json3 = json.loads( device_str_obj3 )
                        for device3 in device_json3:
                            if device3[ 'available' ]:
                                counter_avail3 += 1
                                if counter_avail3 == int( num_sw ):
                                    onos3_dev = True
                                    main.log.info( "All devices have been" +
                                                   " discovered on ONOS3" )
                            else:
                                counter_avail3 = 0
                    if node == 4 and not onos4_dev:
                        main.log.info( "Checking node 4 for device " +
                                       "discovery" )
                        device_str_obj4 = main.ONOS4cli.devices(
                            node_ip=ONOS_ip_list[ 4 ] )
                        device_json4 = json.loads( device_str_obj4 )
                        for device4 in device_json4:
                            if device4[ 'available' ]:
                                counter_avail4 += 1
                                if counter_avail4 == int( num_sw ):
                                    onos4_dev = True
                                    main.log.info( "All devices have been" +
                                                   " discovered on ONOS4" )
                            else:
                                counter_avail4 = 0
                    if node == 5 and not onos5_dev:
                        main.log.info( "Checking node 5 for device " +
                                       "discovery" )
                        device_str_obj5 = main.ONOS5cli.devices(
                            node_ip=ONOS_ip_list[ 5 ] )
                        device_json5 = json.loads( device_str_obj5 )
                        for device5 in device_json5:
                            if device5[ 'available' ]:
                                counter_avail5 += 1
                                if counter_avail5 == int( num_sw ):
                                    onos5_dev = True
                                    main.log.info( "All devices have been" +
                                                   " discovered on ONOS5" )
                            else:
                                counter_avail5 = 0
                    if node == 6 and not onos6_dev:
                        main.log.info( "Checking node 6 for device " +
                                       "discovery" )
                        device_str_obj6 = main.ONOS6cli.devices(
                            node_ip=ONOS_ip_list[ 6 ] )
                        device_json6 = json.loads( device_str_obj6 )
                        for device6 in device_json6:
                            if device6[ 'available' ]:
                                counter_avail6 += 1
                                if counter_avail6 == int( num_sw ):
                                    onos6_dev = True
                                    main.log.info( "All devices have been" +
                                                   " discovered on ONOS6" )
                            else:
                                counter_avail6 = 0
                    if node == 7 and not onos7_dev:
                        main.log.info( "Checking node 7 for device " +
                                       "discovery" )
                        device_str_obj7 = main.ONOS7cli.devices(
                            node_ip=ONOS_ip_list[ 7 ] )
                        device_json7 = json.loads( device_str_obj7 )
                        for device7 in device_json7:
                            if device7[ 'available' ]:
                                counter_avail7 += 1
                                if counter_avail7 == int( num_sw ):
                                    onos7_dev = True
                                    main.log.info( "All devices have been" +
                                                   " discovered on ONOS7" )
                            else:
                                counter_avail7 = 0
                    # END node loop

                # TODO: clean up this mess of an if statements if possible
                # Treat each if as a separate test case with the given
                #     cluster count. Hence when the cluster count changes
                #     the desired calculations will be made
                if cluster_count == 1:
                    if onos1_dev:
                        main.log.info( "All devices have been discovered" +
                                       " on all ONOS instances" )
                        time.sleep( 5 )
                        json_str_metrics_1 =\
                            main.ONOS1cli.topology_events_metrics()
                        json_obj_1 = json.loads( json_str_metrics_1 )
                        graph_timestamp_1 =\
                            json_obj_1[ graphTimestamp ][ 'value' ]

                        graph_lat_1 = \
                            int( graph_timestamp_1 ) - int( t0_system )

                        main.log.info( "Graph Timestamp ONOS1: " +
                                       str( graph_timestamp_1 ) )

                        if graph_lat_1 > sw_disc_threshold_min\
                                and graph_lat_1 < sw_disc_threshold_max\
                                and int( i ) > iter_ignore:
                            sw_discovery_lat_list.append(
                                graph_lat_1 )
                            main.log.info(
                                "Sw discovery latency of " +
                                str( cluster_count ) +
                                " node(s): " +
                                str( graph_lat_1 ) +
                                " ms" )
                        else:
                            main.log.info( "Switch discovery latency " +
                                           "exceeded the threshold." )
                            main.log.info( str( graph_lat_1 ) + " ms" )
                        # Break while loop
                        break
                if cluster_count == 2:
                    if onos1_dev and onos2_dev:
                        main.log.info( "All devices have been discovered" +
                                       " on all " + str( cluster_count ) +
                                       " ONOS instances" )
                        time.sleep( 5 )

                        json_str_metrics_1 =\
                            main.ONOS1cli.topology_events_metrics()
                        json_str_metrics_2 =\
                            main.ONOS2cli.topology_events_metrics()
                        json_obj_1 = json.loads( json_str_metrics_1 )
                        json_obj_2 = json.loads( json_str_metrics_2 )
                        graph_timestamp_1 =\
                            json_obj_1[ graphTimestamp ][ 'value' ]
                        graph_timestamp_2 =\
                            json_obj_2[ graphTimestamp ][ 'value' ]

                        graph_lat_1 = \
                            int( graph_timestamp_1 ) - int( t0_system )
                        graph_lat_2 = \
                            int( graph_timestamp_2 ) - int( t0_system )

                        main.log.info( "Graph Timestamp ONOS1: " +
                                       str( graph_timestamp_1 ) )
                        main.log.info( "Graph Timestamp ONOS2: " +
                                       str( graph_timestamp_2 ) )

                        max_graph_lat = max( graph_lat_1,
                                             graph_lat_2, graph_lat_3 )

                        if max_graph_lat > sw_disc_threshold_min\
                                and max_graph_lat < sw_disc_threshold_max\
                                and int( i ) > iter_ignore:
                            sw_discovery_lat_list.append(
                                max_graph_lat )
                            main.log.info(
                                "Sw discovery latency of " +
                                str( cluster_count ) +
                                " node(s): " +
                                str( max_graph_lat ) +
                                " ms" )
                        else:
                            main.log.info( "Switch discovery latency " +
                                           "exceeded the threshold." )
                            main.log.info( str( max_graph_lat ) + " ms" )
                        break
                if cluster_count == 3:
                    if onos1_dev and onos2_dev and onos3_dev:
                        main.log.info( "All devices have been discovered" +
                                       " on all " + str( cluster_count ) +
                                       " ONOS instances" )

                        # TODO: Investigate this sleep
                        #      added to 'pad' the results with
                        #      plenty of time to 'catch up'
                        time.sleep( 5 )

                        json_str_metrics_1 =\
                            main.ONOS1cli.topology_events_metrics()
                        json_str_metrics_2 =\
                            main.ONOS2cli.topology_events_metrics()
                        json_str_metrics_3 =\
                            main.ONOS3cli.topology_events_metrics()
                        json_obj_1 = json.loads( json_str_metrics_1 )
                        json_obj_2 = json.loads( json_str_metrics_2 )
                        json_obj_3 = json.loads( json_str_metrics_3 )
                        graph_timestamp_1 =\
                            json_obj_1[ graphTimestamp ][ 'value' ]
                        graph_timestamp_2 =\
                            json_obj_2[ graphTimestamp ][ 'value' ]
                        graph_timestamp_3 =\
                            json_obj_3[ graphTimestamp ][ 'value' ]

                        graph_lat_1 = \
                            int( graph_timestamp_1 ) - int( t0_system )
                        graph_lat_2 = \
                            int( graph_timestamp_2 ) - int( t0_system )
                        graph_lat_3 = \
                            int( graph_timestamp_3 ) - int( t0_system )

                        main.log.info( "Graph Timestamp ONOS1: " +
                                       str( graph_timestamp_1 ) )
                        main.log.info( "Graph Timestamp ONOS2: " +
                                       str( graph_timestamp_2 ) )
                        main.log.info( "Graph Timestamp ONOS3: " +
                                       str( graph_timestamp_3 ) )

                        max_graph_lat = max( graph_lat_1,
                                             graph_lat_2,
                                             graph_lat_3 )

                        if max_graph_lat > sw_disc_threshold_min\
                                and max_graph_lat < sw_disc_threshold_max\
                                and int( i ) > iter_ignore:
                            sw_discovery_lat_list.append(
                                max_graph_lat )
                            main.log.info(
                                "Sw discovery latency of " +
                                str( cluster_count ) +
                                " node(s): " +
                                str( max_graph_lat ) +
                                " ms" )
                        else:
                            main.log.info( "Switch discovery latency " +
                                           "exceeded the threshold." )
                            main.log.info( str( max_graph_lat ) + " ms" )

                        break
                if cluster_count == 4:
                    if onos1_dev and onos2_dev and onos3_dev and\
                       onos4_dev:
                        main.log.info( "All devices have been discovered" +
                                       " on all ONOS instances" )
                        json_str_metrics_1 =\
                            main.ONOS1cli.topology_events_metrics()
                        json_str_metrics_2 =\
                            main.ONOS2cli.topology_events_metrics()
                        json_str_metrics_3 =\
                            main.ONOS3cli.topology_events_metrics()
                        json_str_metrics_4 =\
                            main.ONOS4cli.topology_events_metrics()
                        json_obj_1 = json.loads( json_str_metrics_1 )
                        json_obj_2 = json.loads( json_str_metrics_2 )
                        json_obj_3 = json.loads( json_str_metrics_3 )
                        json_obj_4 = json.loads( json_str_metrics_4 )
                        graph_timestamp_1 =\
                            json_obj_1[ graphTimestamp ][ 'value' ]
                        graph_timestamp_2 =\
                            json_obj_2[ graphTimestamp ][ 'value' ]
                        graph_timestamp_3 =\
                            json_obj_3[ graphTimestamp ][ 'value' ]
                        graph_timestamp_4 =\
                            json_obj_4[ graphTimestamp ][ 'value' ]

                        graph_lat_1 = \
                            int( graph_timestamp_1 ) - int( t0_system )
                        graph_lat_2 = \
                            int( graph_timestamp_2 ) - int( t0_system )
                        graph_lat_3 = \
                            int( graph_timestamp_3 ) - int( t0_system )
                        graph_lat_4 = \
                            int( graph_timestamp_4 ) - int( t0_system )

                        main.log.info( "Graph Timestamp ONOS1: " +
                                       str( graph_timestamp_1 ) )
                        main.log.info( "Graph Timestamp ONOS2: " +
                                       str( graph_timestamp_2 ) )
                        main.log.info( "Graph Timestamp ONOS3: " +
                                       str( graph_timestamp_3 ) )
                        main.log.info( "Graph Timestamp ONOS4: " +
                                       str( graph_timestamp_4 ) )

                        max_graph_lat = max( graph_lat_1,
                                             graph_lat_2,
                                             graph_lat_3,
                                             graph_lat_4 )

                        if max_graph_lat > sw_disc_threshold_min\
                                and max_graph_lat < sw_disc_threshold_max\
                                and int( i ) > iter_ignore:
                            sw_discovery_lat_list.append(
                                max_graph_lat )
                            main.log.info(
                                "Sw discovery latency of " +
                                str( cluster_count ) +
                                " node(s): " +
                                str( max_graph_lat ) +
                                " ms" )
                        else:
                            main.log.info( "Switch discovery latency " +
                                           "exceeded the threshold." )
                            main.log.info( str( max_graph_lat ) + " ms" )

                        break
                if cluster_count == 5:
                    if onos1_dev and onos2_dev and onos3_dev and\
                       onos4_dev and onos5_dev:
                        main.log.info( "All devices have been discovered" +
                                       " on all ONOS instances" )

                        # TODO: Investigate this sleep
                        #      added to 'pad' the results with
                        #      plenty of time to 'catch up'
                        time.sleep( 5 )

                        json_str_metrics_1 =\
                            main.ONOS1cli.topology_events_metrics()
                        json_str_metrics_2 =\
                            main.ONOS2cli.topology_events_metrics()
                        json_str_metrics_3 =\
                            main.ONOS3cli.topology_events_metrics()
                        json_str_metrics_4 =\
                            main.ONOS4cli.topology_events_metrics()
                        json_str_metrics_5 =\
                            main.ONOS5cli.topology_events_metrics()
                        json_obj_1 = json.loads( json_str_metrics_1 )
                        json_obj_2 = json.loads( json_str_metrics_2 )
                        json_obj_3 = json.loads( json_str_metrics_3 )
                        json_obj_4 = json.loads( json_str_metrics_4 )
                        json_obj_5 = json.loads( json_str_metrics_5 )
                        graph_timestamp_1 =\
                            json_obj_1[ graphTimestamp ][ 'value' ]
                        graph_timestamp_2 =\
                            json_obj_2[ graphTimestamp ][ 'value' ]
                        graph_timestamp_3 =\
                            json_obj_3[ graphTimestamp ][ 'value' ]
                        graph_timestamp_4 =\
                            json_obj_4[ graphTimestamp ][ 'value' ]
                        graph_timestamp_5 =\
                            json_obj_5[ graphTimestamp ][ 'value' ]

                        graph_lat_1 = \
                            int( graph_timestamp_1 ) - int( t0_system )
                        graph_lat_2 = \
                            int( graph_timestamp_2 ) - int( t0_system )
                        graph_lat_3 = \
                            int( graph_timestamp_3 ) - int( t0_system )
                        graph_lat_4 = \
                            int( graph_timestamp_4 ) - int( t0_system )
                        graph_lat_5 = \
                            int( graph_timestamp_5 ) - int( t0_system )

                        main.log.info( "Graph Timestamp ONOS1: " +
                                       str( graph_timestamp_1 ) )
                        main.log.info( "Graph Timestamp ONOS2: " +
                                       str( graph_timestamp_2 ) )
                        main.log.info( "Graph Timestamp ONOS3: " +
                                       str( graph_timestamp_3 ) )
                        main.log.info( "Graph Timestamp ONOS4: " +
                                       str( graph_timestamp_4 ) )
                        main.log.info( "Graph Timestamp ONOS5: " +
                                       str( graph_timestamp_5 ) )

                        max_graph_lat = max( graph_lat_1,
                                             graph_lat_2,
                                             graph_lat_3,
                                             graph_lat_4,
                                             graph_lat_5 )

                        if max_graph_lat > sw_disc_threshold_min\
                                and max_graph_lat < sw_disc_threshold_max\
                                and int( i ) > iter_ignore:
                            sw_discovery_lat_list.append(
                                max_graph_lat )
                            main.log.info(
                                "Sw discovery latency of " +
                                str( cluster_count ) +
                                " node(s): " +
                                str( max_graph_lat ) +
                                " ms" )
                        else:
                            main.log.info( "Switch discovery latency " +
                                           "exceeded the threshold." )
                            main.log.info( str( max_graph_lat ) + " ms" )

                        break
                if cluster_count == 6:
                    if onos1_dev and onos2_dev and onos3_dev and\
                       onos4_dev and onos5_dev and onos6_dev:
                        main.log.info( "All devices have been discovered" +
                                       " on all ONOS instances" )
                        json_str_metrics_1 =\
                            main.ONOS1cli.topology_events_metrics()
                        json_str_metrics_2 =\
                            main.ONOS2cli.topology_events_metrics()
                        json_str_metrics_3 =\
                            main.ONOS3cli.topology_events_metrics()
                        json_str_metrics_4 =\
                            main.ONOS4cli.topology_events_metrics()
                        json_str_metrics_5 =\
                            main.ONOS5cli.topology_events_metrics()
                        json_str_metrics_6 =\
                            main.ONOS6cli.topology_events_metrics()
                        json_obj_1 = json.loads( json_str_metrics_1 )
                        json_obj_2 = json.loads( json_str_metrics_2 )
                        json_obj_3 = json.loads( json_str_metrics_3 )
                        json_obj_4 = json.loads( json_str_metrics_4 )
                        json_obj_5 = json.loads( json_str_metrics_5 )
                        json_obj_6 = json.loads( json_str_metrics_6 )
                        graph_timestamp_1 =\
                            json_obj_1[ graphTimestamp ][ 'value' ]
                        graph_timestamp_2 =\
                            json_obj_2[ graphTimestamp ][ 'value' ]
                        graph_timestamp_3 =\
                            json_obj_3[ graphTimestamp ][ 'value' ]
                        graph_timestamp_4 =\
                            json_obj_4[ graphTimestamp ][ 'value' ]
                        graph_timestamp_5 =\
                            json_obj_5[ graphTimestamp ][ 'value' ]
                        graph_timestamp_6 =\
                            json_obj_6[ graphTimestamp ][ 'value' ]

                        graph_lat_1 = \
                            int( graph_timestamp_1 ) - int( t0_system )
                        graph_lat_2 = \
                            int( graph_timestamp_2 ) - int( t0_system )
                        graph_lat_3 = \
                            int( graph_timestamp_3 ) - int( t0_system )
                        graph_lat_4 = \
                            int( graph_timestamp_4 ) - int( t0_system )
                        graph_lat_5 = \
                            int( graph_timestamp_5 ) - int( t0_system )
                        graph_lat_6 = \
                            int( graph_timestamp_6 ) - int( t0_system )

                        main.log.info( "Graph Timestamp ONOS1: " +
                                       str( graph_timestamp_1 ) )
                        main.log.info( "Graph Timestamp ONOS2: " +
                                       str( graph_timestamp_2 ) )
                        main.log.info( "Graph Timestamp ONOS3: " +
                                       str( graph_timestamp_3 ) )
                        main.log.info( "Graph Timestamp ONOS4: " +
                                       str( graph_timestamp_4 ) )
                        main.log.info( "Graph Timestamp ONOS5: " +
                                       str( graph_timestamp_5 ) )
                        main.log.info( "Graph Timestamp ONOS6: " +
                                       str( graph_timestamp_6 ) )

                        max_graph_lat = max( graph_lat_1,
                                             graph_lat_2,
                                             graph_lat_3,
                                             graph_lat_4,
                                             graph_lat_5,
                                             graph_lat_6 )

                        if max_graph_lat > sw_disc_threshold_min\
                                and max_graph_lat < sw_disc_threshold_max\
                                and int( i ) > iter_ignore:
                            sw_discovery_lat_list.append(
                                max_graph_lat )
                            main.log.info(
                                "Sw discovery latency of " +
                                str( cluster_count ) +
                                " node(s): " +
                                str( max_graph_lat ) +
                                " ms" )
                        else:
                            main.log.info( "Switch discovery latency " +
                                           "exceeded the threshold." )
                            main.log.info( str( max_graph_lat ) + " ms" )

                        break
                if cluster_count == 7:
                    if onos1_dev and onos2_dev and onos3_dev and\
                       onos4_dev and onos5_dev and onos6_dev and\
                       onos7_dev:
                        main.log.info( "All devices have been discovered" +
                                       " on all ONOS instances" )

                        # TODO: Investigate this sleep
                        #      added to 'pad' the results with
                        #      plenty of time to 'catch up'
                        time.sleep( 5 )

                        json_str_metrics_1 =\
                            main.ONOS1cli.topology_events_metrics()
                        json_str_metrics_2 =\
                            main.ONOS2cli.topology_events_metrics()
                        json_str_metrics_3 =\
                            main.ONOS3cli.topology_events_metrics()
                        json_str_metrics_4 =\
                            main.ONOS4cli.topology_events_metrics()
                        json_str_metrics_5 =\
                            main.ONOS5cli.topology_events_metrics()
                        json_str_metrics_6 =\
                            main.ONOS6cli.topology_events_metrics()
                        json_str_metrics_7 =\
                            main.ONOS7cli.topology_events_metrics()
                        json_obj_1 = json.loads( json_str_metrics_1 )
                        json_obj_2 = json.loads( json_str_metrics_2 )
                        json_obj_3 = json.loads( json_str_metrics_3 )
                        json_obj_4 = json.loads( json_str_metrics_4 )
                        json_obj_5 = json.loads( json_str_metrics_5 )
                        json_obj_6 = json.loads( json_str_metrics_6 )
                        json_obj_7 = json.loads( json_str_metrics_7 )
                        graph_timestamp_1 =\
                            json_obj_1[ graphTimestamp ][ 'value' ]
                        graph_timestamp_2 =\
                            json_obj_2[ graphTimestamp ][ 'value' ]
                        graph_timestamp_3 =\
                            json_obj_3[ graphTimestamp ][ 'value' ]
                        graph_timestamp_4 =\
                            json_obj_4[ graphTimestamp ][ 'value' ]
                        graph_timestamp_5 =\
                            json_obj_5[ graphTimestamp ][ 'value' ]
                        graph_timestamp_6 =\
                            json_obj_6[ graphTimestamp ][ 'value' ]
                        graph_timestamp_7 =\
                            json_obj_7[ graphTimestamp ][ 'value' ]

                        graph_lat_1 = \
                            int( graph_timestamp_1 ) - int( t0_system )
                        graph_lat_2 = \
                            int( graph_timestamp_2 ) - int( t0_system )
                        graph_lat_3 = \
                            int( graph_timestamp_3 ) - int( t0_system )
                        graph_lat_4 = \
                            int( graph_timestamp_4 ) - int( t0_system )
                        graph_lat_5 = \
                            int( graph_timestamp_5 ) - int( t0_system )
                        graph_lat_6 = \
                            int( graph_timestamp_6 ) - int( t0_system )
                        graph_lat_7 = \
                            int( graph_timestamp_7 ) - int( t0_system )

                        main.log.info( "Graph Timestamp ONOS1: " +
                                       str( graph_timestamp_1 ) )
                        main.log.info( "Graph Timestamp ONOS2: " +
                                       str( graph_timestamp_2 ) )
                        main.log.info( "Graph Timestamp ONOS3: " +
                                       str( graph_timestamp_3 ) )
                        main.log.info( "Graph Timestamp ONOS4: " +
                                       str( graph_timestamp_4 ) )
                        main.log.info( "Graph Timestamp ONOS5: " +
                                       str( graph_timestamp_5 ) )
                        main.log.info( "Graph Timestamp ONOS6: " +
                                       str( graph_timestamp_6 ) )
                        main.log.info( "Graph Timestamp ONOS7: " +
                                       str( graph_timestamp_7 ) )

                        max_graph_lat = max( graph_lat_1,
                                             graph_lat_2,
                                             graph_lat_3,
                                             graph_lat_4,
                                             graph_lat_5,
                                             graph_lat_6,
                                             graph_lat_7 )

                        if max_graph_lat > sw_disc_threshold_min\
                                and max_graph_lat < sw_disc_threshold_max\
                                and int( i ) > iter_ignore:
                            sw_discovery_lat_list.append(
                                max_graph_lat )
                            main.log.info(
                                "Sw discovery latency of " +
                                str( cluster_count ) +
                                " node(s): " +
                                str( max_graph_lat ) +
                                " ms" )
                        else:
                            main.log.info( "Switch discovery latency " +
                                           "exceeded the threshold." )
                            main.log.info( str( max_graph_lat ) + " ms" )

                        break

                counter_loop += 1
                time.sleep( 3 )
                # END WHILE LOOP

            # Below is used for reporting SYN / ACK timing
            # of all switches
            main.ONOS1.tshark_stop()
            syn_ack_timestamp_list = []
            if cluster_count < 3:
                # TODO: capture synack on nodes less than 3
                syn_ack_timestamp_list.append( 0 )

            if cluster_count >= 3:
                main.ONOS2.tshark_stop()
                main.ONOS3.tshark_stop()
                time.sleep( 5 )
                os.system(
                    "scp " +
                    ONOS_user +
                    "@" +
                    ONOS1_ip +
                    ":" +
                    "/tmp/syn_ack_onos1_iter" +
                    str( i ) +
                    ".txt /tmp/" )
                os.system(
                    "scp " +
                    ONOS_user +
                    "@" +
                    ONOS2_ip +
                    ":" +
                    "/tmp/syn_ack_onos2_iter" +
                    str( i ) +
                    ".txt /tmp/" )
                os.system(
                    "scp " +
                    ONOS_user +
                    "@" +
                    ONOS3_ip +
                    ":" +
                    "/tmp/syn_ack_onos3_iter" +
                    str( i ) +
                    ".txt /tmp/" )
                time.sleep( 5 )
                # Read each of the files and append all
                # SYN / ACK timestamps to the list
                with open( "/tmp/syn_ack_onos1_iter" + str( i ) + ".txt" ) as\
                        f_onos1:
                    for line in f_onos1:
                        line = line.split( " " )
                        try:
                            float( line[ 1 ] )
                            syn_ack_timestamp_list.append( line[ 1 ] )
                        except ValueError:
                            main.log.info( "String cannot be converted" )
                with open( "/tmp/syn_ack_onos2_iter" + str( i ) + ".txt" ) as\
                        f_onos2:
                    for line in f_onos2:
                        line = line.split( " " )
                        try:
                            float( line[ 1 ] )
                            syn_ack_timestamp_list.append( line[ 1 ] )
                        except ValueError:
                            main.log.info( "String cannot be converted" )
                with open( "/tmp/syn_ack_onos3_iter" + str( i ) + ".txt" ) as\
                        f_onos3:
                    for line in f_onos3:
                        line = line.split( " " )
                        try:
                            float( line[ 1 ] )
                            syn_ack_timestamp_list.append( line[ 1 ] )
                        except ValueError:
                            main.log.info( "String cannot be converted" )
            if cluster_count >= 4:
                main.ONOS4.tshark_stop()
                time.sleep( 5 )
                os.system(
                    "scp " +
                    ONOS_user +
                    "@" +
                    ONOS4_ip +
                    ":" +
                    "/tmp/syn_ack_onos4_iter" +
                    str( i ) +
                    ".txt /tmp/" )
                time.sleep( 5 )
                with open( "/tmp/syn_ack_onos4_iter" + str( i ) + ".txt" ) as\
                        f_onos4:
                    for line in f_onos4:
                        line = line.split( " " )
                        try:
                            float( line[ 1 ] )
                            syn_ack_timestamp_list.append( line[ 1 ] )
                        except ValueError:
                            main.log.info( "String cannot be converted" )
            if cluster_count >= 5:
                main.ONOS5.tshark_stop()
                time.sleep( 5 )
                os.system(
                    "scp " +
                    ONOS_user +
                    "@" +
                    ONOS5_ip +
                    ":" +
                    "/tmp/syn_ack_onos5_iter" +
                    str( i ) +
                    ".txt /tmp/" )
                time.sleep( 5 )
                with open( "/tmp/syn_ack_onos5_iter" + str( i ) + ".txt" ) as\
                        f_onos5:
                    for line in f_onos5:
                        line = line.split( " " )
                        try:
                            float( line[ 1 ] )
                            syn_ack_timestamp_list.append( line[ 1 ] )
                        except ValueError:
                            main.log.info( "String cannot be converted" )
            if cluster_count >= 6:
                main.ONOS6.tshark_stop()
                time.sleep( 5 )
                os.system(
                    "scp " +
                    ONOS_user +
                    "@" +
                    ONOS6_ip +
                    ":" +
                    "/tmp/syn_ack_onos6_iter" +
                    str( i ) +
                    ".txt /tmp/" )
                time.sleep( 5 )
                with open( "/tmp/syn_ack_onos6_iter" + str( i ) + ".txt" ) as\
                        f_onos6:
                    for line in f_onos6:
                        line = line.split( " " )
                        try:
                            float( line[ 1 ] )
                            syn_ack_timestamp_list.append( line[ 1 ] )
                        except ValueError:
                            main.log.info( "String cannot be converted" )
            if cluster_count == 7:
                main.ONOS7.tshark_stop()
                time.sleep( 5 )
                os.system(
                    "scp " +
                    ONOS_user +
                    "@" +
                    ONOS7_ip +
                    ":" +
                    "/tmp/syn_ack_onos7_iter" +
                    str( i ) +
                    ".txt /tmp/" )
                time.sleep( 5 )
                with open( "/tmp/syn_ack_onos7_iter" + str( i ) + ".txt" ) as\
                        f_onos7:
                    for line in f_onos7:
                        line = line.split( " " )
                        try:
                            float( line[ 1 ] )
                            syn_ack_timestamp_list.append( line[ 1 ] )
                        except ValueError:
                            main.log.info( "String cannot be converted" )

            # Sort the list by timestamp
            syn_ack_timestamp_list = sorted( syn_ack_timestamp_list )
            print "syn_ack_-1  " + str( syn_ack_timestamp_list )

            syn_ack_delta =\
                int( float( syn_ack_timestamp_list[ -1 ] ) * 1000 ) -\
                int( float( syn_ack_timestamp_list[ 0 ] ) * 1000 )

            main.log.info( "Switch connection attempt delta iteration " +
                           str( i ) + ": " + str( syn_ack_delta ) )
            syn_ack_delta_list.append( syn_ack_delta )
            # END ITERATION LOOP
        # REPORT HERE

        if len( sw_discovery_lat_list ) > 0:
            sw_lat_avg = sum( sw_discovery_lat_list ) / \
                len( sw_discovery_lat_list )
            sw_lat_dev = numpy.std( sw_discovery_lat_list )
        else:
            sw_lat_avg = 0
            sw_lat_dev = 0
            assertion = main.FALSE

        main.log.report( "Switch connection attempt time avg " +
                         "(last sw SYN/ACK time - first sw SYN/ACK time) " +
                         str( sum( syn_ack_delta_list ) /
                              len( syn_ack_delta_list ) ) +
                         " ms" )
        main.log.report( str( num_sw ) + " Switch discovery lat for " +
                         str( cluster_count ) + " instance(s): " )
        main.log.report( "Avg: " +
                         str( sw_lat_avg ) +
                         " ms  " +
                         "Std Deviation: " +
                         str( round( sw_lat_dev, 1 ) ) +
                         " ms" )

        utilities.assert_equals(
            expect=main.TRUE,
            actual=assertion,
            onpass="Switch discovery convergence latency" +
            " for " +
            str( cluster_count ) +
            " nodes successful",
            onfail="Switch discovery convergence latency" +
            " test failed" )

    def CASE3( self, main ):
        """
        Increase number of nodes and initiate CLI
        """
        import time
        import subprocess
        import os
        import requests
        import json

        ONOS1_ip = main.params[ 'CTRL' ][ 'ip1' ]
        ONOS2_ip = main.params[ 'CTRL' ][ 'ip2' ]
        ONOS3_ip = main.params[ 'CTRL' ][ 'ip3' ]
        ONOS4_ip = main.params[ 'CTRL' ][ 'ip4' ]
        ONOS5_ip = main.params[ 'CTRL' ][ 'ip5' ]
        ONOS6_ip = main.params[ 'CTRL' ][ 'ip6' ]
        ONOS7_ip = main.params[ 'CTRL' ][ 'ip7' ]

        cell_name = main.params[ 'ENV' ][ 'cellName' ]

        MN1_ip = main.params[ 'MN' ][ 'ip1' ]
        BENCH_ip = main.params[ 'BENCH' ][ 'ip' ]

        # NOTE:We start with cluster_count at 3. The first
        # case already initialized ONOS1. Increase the
        # cluster count and start from 3.
        # You can optionally change the increment to
        # test steps of node sizes, such as 3,5,7

        global cluster_count
        cluster_count += 2
        main.log.report( "Increasing cluster size to " +
                         str( cluster_count ) )

        install_result = main.FALSE
        # Supports up to 7 node configuration
        # TODO: Cleanup this ridiculous repetitive code
        if cluster_count == 3:
            install_result = \
                main.ONOSbench.onos_install( node=ONOS2_ip )
            install_result = \
                main.ONOSbench.onos_install( node=ONOS3_ip )
            time.sleep( 5 )
            main.log.info( "Starting CLI" )
            main.ONOS2cli.start_onos_cli( ONOS2_ip )
            main.ONOS3cli.start_onos_cli( ONOS3_ip )
            main.ONOS1cli.add_node( ONOS2_ip, ONOS2_ip )
            main.ONOS1cli.add_node( ONOS3_ip, ONOS3_ip )

        if cluster_count == 4:
            main.log.info( "Installing ONOS on node 4" )
            install_result = \
                main.ONOSbench.onos_install( node=ONOS4_ip )
            time.sleep( 5 )
            main.log.info( "Starting CLI" )
            main.ONOS4cli.start_onos_cli( ONOS4_ip )
            main.ONOS1cli.add_node( ONOS4_ip, ONOS4_ip )

        elif cluster_count == 5:
            main.log.info( "Installing ONOS on nodes 4 and 5" )
            install_result2 = \
                main.ONOSbench.onos_install( options="", node=ONOS4_ip )
            install_result3 = \
                main.ONOSbench.onos_install( options="", node=ONOS5_ip )
            time.sleep( 5 )
            main.log.info( "Starting CLI" )
            main.ONOS4cli.start_onos_cli( ONOS4_ip )
            main.ONOS5cli.start_onos_cli( ONOS5_ip )
            main.ONOS1cli.add_node( ONOS4_ip, ONOS4_ip )
            main.ONOS1cli.add_node( ONOS5_ip, ONOS5_ip )
            install_result = install_result2 and install_result3

        elif cluster_count == 6:
            main.log.info( "Installing ONOS on nodes 4, 5,and 6" )
            install_result1 = \
                main.ONOSbench.onos_install( options="", node=ONOS4_ip )
            install_result2 = \
                main.ONOSbench.onos_install( options="", node=ONOS5_ip )
            install_result3 = \
                main.ONOSbench.onos_install( node=ONOS6_ip )
            time.sleep( 5 )
            main.log.info( "Starting CLI" )
            main.ONOS4cli.start_onos_cli( ONOS4_ip )
            main.ONOS5cli.start_onos_cli( ONOS5_ip )
            main.ONOS6cli.start_onos_cli( ONOS6_ip )
            main.ONOS1cli.add_node( ONOS4_ip, ONOS4_ip )
            main.ONOS1cli.add_node( ONOS5_ip, ONOS5_ip )
            main.ONOS1cli.add_node( ONOS6_ip, ONOS6_ip )
            install_result = install_result1 and install_result2 and\
                install_result3

        elif cluster_count == 7:
            main.log.info( "Installing ONOS on nodes 4, 5, 6,and 7" )
            install_result3 = \
                main.ONOSbench.onos_install( node=ONOS6_ip )
            install_result4 = \
                main.ONOSbench.onos_install( node=ONOS7_ip )
            main.log.info( "Starting CLI" )
            main.ONOS4cli.start_onos_cli( ONOS4_ip )
            main.ONOS5cli.start_onos_cli( ONOS5_ip )
            main.ONOS6cli.start_onos_cli( ONOS6_ip )
            main.ONOS7cli.start_onos_cli( ONOS7_ip )
            main.ONOS1cli.add_node( ONOS4_ip, ONOS4_ip )
            main.ONOS1cli.add_node( ONOS5_ip, ONOS5_ip )
            main.ONOS1cli.add_node( ONOS6_ip, ONOS6_ip )
            main.ONOS1cli.add_node( ONOS7_ip, ONOS7_ip )

            install_result = \
                install_result3 and install_result4

        time.sleep( 5 )

        if install_result == main.TRUE:
            assertion = main.TRUE
        else:
            assertion = main.FALSE

        utilities.assert_equals(
            expect=main.TRUE,
            actual=assertion,
            onpass="Scale out to " +
            str( cluster_count ) +
            " nodes successful",
            onfail="Scale out to " +
            str( cluster_count ) +
            " nodes failed" )

    def CASE4( self, main ):
        """
        Cleanup ONOS nodes and Increase topology size
        """
        # TODO: use meaningful assertion
        assertion = main.TRUE

        ONOS1_ip = main.params[ 'CTRL' ][ 'ip1' ]
        ONOS2_ip = main.params[ 'CTRL' ][ 'ip2' ]
        ONOS3_ip = main.params[ 'CTRL' ][ 'ip3' ]
        ONOS4_ip = main.params[ 'CTRL' ][ 'ip4' ]
        ONOS5_ip = main.params[ 'CTRL' ][ 'ip5' ]
        ONOS6_ip = main.params[ 'CTRL' ][ 'ip6' ]
        ONOS7_ip = main.params[ 'CTRL' ][ 'ip7' ]
        MN1_ip = main.params[ 'MN' ][ 'ip1' ]
        BENCH_ip = main.params[ 'BENCH' ][ 'ip' ]

        main.log.info( "Uninstalling previous instances" )
        main.ONOSbench.onos_uninstall( node_ip=ONOS2_ip )
        main.ONOSbench.onos_uninstall( node_ip=ONOS3_ip )
        main.ONOSbench.onos_uninstall( node_ip=ONOS4_ip )
        main.ONOSbench.onos_uninstall( node_ip=ONOS5_ip )
        main.ONOSbench.onos_uninstall( node_ip=ONOS6_ip )
        main.ONOSbench.onos_uninstall( node_ip=ONOS7_ip )

        global topo_iteration
        global cluster_count
        cluster_count = 1
        topo_iteration += 1

        main.log.report( "Increasing topology size" )
        utilities.assert_equals( expect=main.TRUE, actual=assertion,
                                 onpass="Topology size increased successfully",
                                 onfail="Topology size was not increased" )
