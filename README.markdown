zfs
===

Installs zfs, configures zfs pools and file systems.

Installation
------------

- Debian buster: builds zfs-dkms using backports
- Debian bullseye: builds zfs-dkms using stable
- Ubuntu: uses the shipped version

If `modprobe zfs` fails, a reboot into the uptodate kernel may be needed.

Configuration
-------------

The [zfs_arc_max](https://openzfs.github.io/openzfs-docs/Performance%20and%20Tuning/Module%20Parameters.html#zfs-arc-max) module parameter may need tuning. Reduce if ARC competes too much with other applications, increase if ZFS is the primary application and can use more RAM.

Default config (uses default of RAM size in bytes / 2):

```yaml
zfs_module_config_arc_max_gb: 0
```

Example config (8 GiB):

```yaml
zfs_module_config_arc_max_gb: 8
```
