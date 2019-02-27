FAIL=0

for vmName in "$@"; do
    az vm deallocate --resource-group asl17_vms --name $vmName &
    echo "Stopping VM ${vmName}"
done

echo "Waiting for shutdown completion"
for job in `jobs -p`
do
    echo "Waiting for job: $job to complete"
    wait $job || let "FAIL+=1"
done


if [ "$FAIL" == "0" ];
then
    echo "Stopping VM's Succeeded!"
    exit 0
else
	echo "Stopping VM's Failed for ${FAIL} machines!"
    exit 1
fi

