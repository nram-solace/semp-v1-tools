ABOUT
============================================================================
SEMPTools is set of python scripts for managing Solace VPNs

This has few python scripts and support scripts
bin/CheckSolaceSetup.py : check VPN config on one or more Solace Router
bin/ClearSolaceStats.py : Clear router/VPN stats 
bin/GetSolaceStats.py   : Collect VPN & Client stats & discard stats
bin/ConfigureSolaceRouter.py : Create and Delete Global (Non-VPN) Solace objects

SAMPLE CONFIG
============================================================================
See input/sample dir.

INSTALLATION
============================================================================
See INSTALL.txt

SAMPLE RUN
============================================================================
See COMMANDS.txt

All Log files are created on the current directory. Look for <Program-name>.log
Eg: CheckSolaceSetup.log       ClearSolaceStats.log       ConfigureSolaceRouter.log  GetSolaceStats.log

All output files are created under out/ directory
Eg:
out/solace_stats.tvo

All SEMP template files used by the scripts are under SEMP/<SEMP_VERSION> directory
Eg: SEMP/8_2VMR//ShowVpnStats.xml

All Request and Response SEMP XML sent to and received from the router are under SEMP/request and SEMP/response
directory respectively, prefixed with <VPNNANE>
Eg:
./SEMP/request/TESTVPN-ShowVpnStats.xml
./SEMP/response/TESTVPN-ShowVpnStats.xml

A copy of respone SEMP files are also stored with timestamp for post timeseries analysis
Eg:
nram@marvin:response$ ls -ltr MarketData-ShowVpnStats*
-rw-r--r--  1 nram  staff  9385 Aug 16 14:18 MarketData-ShowVpnStats_20170816141854.xml
-rw-r--r--  1 nram  staff  9385 Aug 16 14:19 MarketData-ShowVpnStats_20170816141904.xml
-rw-r--r--  1 nram  staff  9385 Aug 16 14:19 MarketData-ShowVpnStats_20170816141914.xml
-rw-r--r--  1 nram  staff  9385 Aug 16 14:19 MarketData-ShowVpnStats_20170816141924.xml
-rw-r--r--  1 nram  staff  9385 Aug 16 14:19 MarketData-ShowVpnStats.xml


CHANGE HISTORY
============================================================================
See HISTORY.txt

LICENSE
============================================================================
See LICENSE.txt
