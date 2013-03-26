all: index.rst

TOPDIR=../../..
MOFS=$(TOPDIR)/mof/base.mof \
    $(TOPDIR)/mof/luks.mof \
    $(TOPDIR)/mof/partitions.mof \
    $(TOPDIR)/mof/storage.mof \
    $(TOPDIR)/mof/filesystem.mof

index.rst: $(MOFS)
	openlmi-doc-class2rst -H header.txt -M `echo $(MOFS) | sed 's/ / -M /g'` -S /usr/share/mof/cim-current/CIM_Schema.mof `cat $(MOFS) | grep "^class" | cut -d ' ' -f 2`
