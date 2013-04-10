all: index.rst

TOPDIR=../../..
MOFS=$(TOPDIR)/mof/LMI_Storage-Base.mof \
    $(TOPDIR)/mof/LMI_Storage-Luks.mof \
    $(TOPDIR)/mof/LMI_Storage-Partitions.mof \
    $(TOPDIR)/mof/LMI_Storage-BlockStorage.mof \
    $(TOPDIR)/mof/LMI_Storage-Filesystem.mof \
    $(TOPDIR)/mof/LMI_Storage-Jobs.mof

index.rst: $(MOFS)
	openlmi-doc-class2rst -H header.txt -M `echo $(MOFS) | sed 's/ / -M /g'` -S /usr/share/mof/cim-current/CIM_Schema.mof -S /usr/share/openlmi-providers/LMI_Qualifiers.mof -S /usr/share/openlmi-providers/LMI_Jobs.mof `cat $(MOFS) | grep "^class" | cut -d ' ' -f 2`
