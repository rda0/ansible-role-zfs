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

### Default pool and filesystem properties

Set default pool props (used if not explicitely defined in `pool.pool_props`):

```yaml
zfs_pool_props:
  autoexpand: 'on'
```

Set default filesystem props (used if not explicitely defined in `[pool|dataset].fs_props`):

```yaml
zfs_fs_props:
  atime: 'off'
  xattr: 'off'
  compression: lz4
  recordsize: 8K
```

### pools

Note: `pool_props` and `fs_props` are applied to pools only during initial creation.

Create 3 pools (zp0, zp1, mypool):

```yaml
zfs_pools:
  - config: raidz2 sda sdb sdc sdd
  - config: >-
      mirror sde sdf
      mirror sdg sdh
      log mirror sdi sdj
      cache sdk sdl
      special mirror sdm sdn
      spare sdo
    pool_props:
      autoexpand: 'on'
      autoreplace: 'on'
    fs_props:
      compression: lz4
      recordsize: 32K
  - name: mypool
    config: mirror sdg sdh mirror sdi sdj
    ashift: 12
    mount: /var/opt/mypool
```

### datasets

Create 3 datasets (on zp0, zp1 and mypool):

```yaml
zfs_datasets:
  - name: zfs0
    mount: /var/opt/zfs0
  - name: zfs1
    pool: zp1
    mount: /var/opt/zfs1
    fs_props:
      compression: lz4
      recordsize: 128K
  - name: myzfs
    pool: mypool
    mount: /var/opt/myzfs
```

### ZFS Block Devices


```yaml
zfs_blockdevices:             # list of ZFS block device descriptions 
  - name: 'vol01'             # mandatory: -> $pool/$name
    size: 10G                 # mandatory: volume size
    pool: 'zp0'               # optional: defaults to zp0
    zfs_options:              # optional: dictionary with zfs options 
      volblocksize: 64K
      refreservation: none
      reservation: none
    filesystem: xfs           # optional: create a filesystem
    fs_options:               # optional: parameters for mkfs.$fs
     ["-b size=2k", "-i maxpct=0", "-l internal,size=32768b,version=2", "-n size=8k,version=2" ]
  - name: 'vol02'             # minimal config
    size: 2G
```
