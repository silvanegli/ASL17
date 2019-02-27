FAIL=0

for vmName in "$@"; do
    az vm start --resource-group asl17_vms --name $vmName &
    echo "Starting VM ${vmName}"
done

echo "Waiting for startup completion"
for job in `jobs -p`
do
    echo "Waiting for job: $job to complete"
    wait $job || let "FAIL+=1"
done

if [ "$FAIL" == "0" ];
then
    echo "Starting VM's Succeeded!"
    exit 0
else
    echo "Starting VM's Failed for ${FAIL} machines!"
    exit 1
fi

