echo
echo "============ CheckSolaceSetup =============="
> CheckSolaceSetup.log; python bin/CheckSolaceSetup.py  --vpn TESTVPN --hostlist input/hostlist.yaml  --sitedefaults input/site-defaults.yaml
echo
echo "============ GetSolaceStats =============="
> GetSolaceStats.log; python bin/GetSolaceStats.py --host vmr16:8000 --vpn TESTVPN --password admin
echo
echo "============ ClearSolaceStats =============="
> ClearSolaceStats.log; python bin/ClearSolaceStats.py  --host vmr16:8000 --vpn TESTVPN --password admin
