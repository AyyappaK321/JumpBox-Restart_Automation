import ssl
import atexit
import pandas as pd
import requests
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
from io import StringIO
 
# Parameters
vcenter_server = "NOAMIND01VCX02.NOAM.FADV.NET"
username = "apac\kopparay"
password = "Prabhakar@1986"
owner_tag = "Owner"
jump_box_name = "jump-box-name"
csv_url = "https://github.com/mishrkan-fadv/JumpBox-Restart_Automation/blob/main/jira_custom_data.csv"  # Replace with your CSV URL
 
def download_csv(csv_url):
    response = requests.get(csv_url)
    response.raise_for_status()  # Raise an error for bad responses
    return pd.read_csv(StringIO(response.text))
 
def get_vm_by_ip_and_hostname(content, ip_address, hostname, owner_tag):
    for datacenter in content.rootFolder.childEntity:
        if hasattr(datacenter, 'vmFolder'):
            for vm in datacenter.vmFolder.childEntity:
                if vm.guest and vm.guest.ipAddress:
                    vm_ip = vm.guest.ipAddress
                    vm_hostname = vm.name
                    tags = [tag.name for tag in vm.tag]
                    owner = next((tag for tag in tags if tag == owner_tag), None)
 
                    if vm_ip == ip_address and vm_hostname == hostname:
                        return vm, owner
    return None, None
 
def reboot_vm(service_instance, vm):
    print(f"Rebooting the jump box: {vm.name}")
    task = vm.PowerOff()  # Power off the VM before reboot
    task.Wait()
    vm.PowerOn()  # Power on the VM after reboot
 
def main():
    # Disable SSL certificate verification
    context = ssl._create_unverified_context()
 
    # Connect to vCenter
    service_instance = SmartConnect(host=vcenter_server, user=username, pwd=password, sslContext=context)
    atexit.register(Disconnect, service_instance)
 
    # Get content
    content = service_instance.RetrieveContent()
 
    # Download CSV and validate VMs
    df = download_csv(csv_url)
 
    for index, row in df.iterrows():
        ip_address = row['ip_address']
        hostname = row['hostname']
        owner = row['owner']
 
        vm, owner_tag_value = get_vm_by_ip_and_hostname(content, ip_address, hostname, owner_tag)
 
        if vm and owner_tag_value:
            print(f"Validation successful for VM: {vm.name}")
            print(f"Owner: {owner_tag_value}")
 
            # Check if it's the jump box and reboot
            if vm.name == jump_box_name:
                reboot_vm(service_instance, vm)
            else:
                print("The VM is not the jump box. No action taken.")
        else:
            print(f"No matching VM found for IP: {ip_address}, Hostname: {hostname}")
 
if __name__ == "__main__":
    main()
