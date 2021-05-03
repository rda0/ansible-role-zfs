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

See `defaults/main.yml` for details.

### Kernel module parameters

The [zfs_arc_max](https://openzfs.github.io/openzfs-docs/Performance%20and%20Tuning/Module%20Parameters.html#zfs-arc-max) module parameter may need tuning. Reduce if ARC competes too much with other applications, increase if ZFS is the primary application and can use more RAM.

Default config (uses default of RAM size in bytes / 2):

```yaml
zfs_module_config_arc_max_gb: 0
```

Example config (8 GiB):

```yaml
zfs_module_config_arc_max_gb: 8
```

### zpools

Set default zpool props (used if not explicitely defined in `zpool.props`):

```yaml
zfs_zpool_props:
  - autoexpand=on
```

Create 3 zpools (zp0, zp1, mypool):

```yaml
zfs_zpools:
  - config: raidz2 sda sdb sdc sdd
  - config: sde sdf
    props:
      - autoexpand=on
      - autoreplace=on
  - name: mypool
    config: mirror sdg sdh mirror sdi sdj
    ashift: 12
```

### datasets

Set default dataset props (used if not explicitely defined in `dataset.props`):

```yaml
zfs_dataset_props:
  atime: off
  xattr: off
  compression: lz4
  recordsize: 8k
```

Create 3 datasets (on zp0, zp1 and mypool):

```yaml
zfs_datasets:
  - name: zfs0
    mount: /var/opt/zfs0
  - name: zfs1
    zpool: zp1
    mount: /var/opt/zfs1
    props:
      compression: lz4
      recordsize: 128k
  - name: myzfs
    zpool: mypool
    mount: /var/opt/myzfs
```
