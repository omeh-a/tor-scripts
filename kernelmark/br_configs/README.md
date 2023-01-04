# br_configs

Put configs named exactly in the form `[machine].config` - make sure you **REMOVE** the line specifing kernel version (somewhere between lines 400 and 500) because kernelmark will append it to the file when it is copied.

You must also remove all kernel custom header properties as these will get re-added. They are of the form 
```
BR2_PACKAGE_HOST_LINUX_HEADERS_CUSTOM_[MAJOR]_[MINOR]
```