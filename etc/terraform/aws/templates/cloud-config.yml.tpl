#cloud-config

hostname: ${hostname}

coreos:
  update:
    reboot-strategy: off
