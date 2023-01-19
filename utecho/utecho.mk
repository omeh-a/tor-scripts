# Makefile for Buildroot to grab. To build this yourself, just use the one in /src
# Based off of https://github.com/cirosantilli/buildroot/tree/out-of-tree-2016.05

UTECHO_VERSION = 1.0
UTECHO_SITE = ./package/utecho/src
UTECHO_SITE_METHOD = local

define UTECHO_BUILD_CMDS
	$(MAKE) CC="$(TARGET_CC)" LD="$(TARGET_LD)" -C $(@D)
endef

define UTECHO_INSTALL_TARGET_CMDS
	$(INSTALL) -D -m 0755 $(@D)/utecho $(TARGET_DIR)/usr/bin
endef

$(eval $(generic-package))
