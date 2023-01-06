# br_configs

Put configs named exactly in the form `[machine].config` - make sure you **REMOVE** the line specifing kernel version (somewhere between lines 400 and 500) because kernelmark will append it to the file when it is copied.

You must also remove all kernel custom header properties as these will get re-added. They are of the form 
```
BR2_PACKAGE_HOST_LINUX_HEADERS_CUSTOM_[MAJOR]_[MINOR]
```

## Garbage to manually remove (add?)

Need to add these lines too because Buildroot is stupid when changing kernel versions. Sanitise does this for you.

```
BR2_PACKAGE_PLY=n
BR2_PACKAGE_OFONO=n
BR2_PACKAGE_KMSXX=n
BR2_PACKAGE_LIBQRTR_GLIB=n
BR2_PACKAGE_ELL=n
BR2_PACKAGE_LIBURING=n
BR2_PACKAGE_CFM=n
BR2_PACKAGE_IWD=n
BR2_PACKAGE_MRP=n
BR2_PACKAGE_OLSR=n
```