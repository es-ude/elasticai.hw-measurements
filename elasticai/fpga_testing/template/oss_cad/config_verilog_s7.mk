.DELETE_ON_ERROR:

ifeq ($(filter xc7%,$(PACKAGE)),)
$(error PACKAGE must be a Xilinx part for DEVICE=S7, e.g. PACKAGE = xc7s50ftgb196-1 (is: '$(PACKAGE)'))
endif

ifneq ($(filter xc7a%,$(PACKAGE)),)
    FAMILY         ?= artix7
else
    FAMILY         ?= spartan7
endif
NEXTPNR_XILINX_DIR ?= /opt/openxc7
PRJXRAY_DB_DIR     ?= $(NEXTPNR_XILINX_DIR)/external/prjxray-db
XILINX_GEN         ?= $(NEXTPNR_XILINX_DIR)/share/nextpnr/himbaechel/uarch/xilinx/gen/xilinx_gen.py
BBASM              ?= $(NEXTPNR_XILINX_DIR)/bin/bbasm
CHIPDB_DIR         ?= $(PRJ_ROOT)/chipdb

DBPART := $(shell echo $(PACKAGE) | sed -e 's/-.*//')
DIE    := $(shell echo $(PACKAGE) | sed -E 's/^(xc7[as][0-9]+t?).*/\1/')
CHIPDB := $(CHIPDB_DIR)/$(DBPART).bin
XDC    := $(SRC_ROOT)/io.xdc

HAVE_FPGA_AS := $(shell command -v fpga-as 2>/dev/null)

VLOG_SRC = $(shell find $(SRC_ROOT)/ -type f \( -iname "*.v" -o -iname "*.sv" \) ! -iname "*_tb.v")
CELLS_SYM := $(shell yosys-config --datdir)/xilinx/cells_sim.v

$(CHIPDB):
	mkdir -p $(CHIPDB_DIR)
	python3 $(XILINX_GEN) --xray $(PRJXRAY_DB_DIR)/$(FAMILY) --device $(DIE) --bba $(CHIPDB_DIR)/$(DBPART).bba
	$(BBASM) -l $(CHIPDB_DIR)/$(DBPART).bba $@
	rm -f $(CHIPDB_DIR)/$(DBPART).bba

.PHONY: synthesize
synthesize: $(BUILD_OUT)/synth/$(TOP).json $(BUILD_OUT)/synth/$(TOP).v

$(BUILD_OUT)/synth/$(TOP).json $(BUILD_OUT)/synth/$(TOP).v: $(VLOG_SRC)
	mkdir -p $(BUILD_OUT)/synth
	yosys \
	    -qql $(BUILD_OUT)/synth/$(TOP).log \
	    -p 'read_verilog -sv $(VLOG_SRC); hierarchy -top $(TOP); synth_xilinx -flatten -abc9 -arch xc7 -top $(TOP); tee -o $(BUILD_OUT)/$(TOP)_util_sync.rpt stat -width; write_json $(BUILD_OUT)/synth/$(TOP).json; write_verilog $(BUILD_OUT)/synth/$(TOP).v;'

$(BUILD_OUT)/impl/$(TOP).fasm: $(BUILD_OUT)/synth/$(TOP).json $(CHIPDB) $(XDC)
	mkdir -p $(BUILD_OUT)/impl
	nextpnr-xilinx \
	    --chipdb $(CHIPDB) \
	    --xdc $(XDC) \
	    --json $< \
	    --fasm $@ \
	    --timing-allow-fail \
	    --freq $(FREQ) \
	    2> $(BUILD_OUT)/$(TOP)_util_impl.rpt

ifneq ($(HAVE_FPGA_AS),)
$(BUILD_OUT)/$(TOP).bit: $(BUILD_OUT)/impl/$(TOP).fasm
	fpga-as --prjxray_db_path=$(PRJXRAY_DB_DIR)/$(FAMILY) --part $(PACKAGE) $< > $@
else
$(BUILD_OUT)/impl/$(TOP).frames: $(BUILD_OUT)/impl/$(TOP).fasm
	openxc7-fasm2frames --part $(PACKAGE) --db-root $(PRJXRAY_DB_DIR)/$(FAMILY) $< > $@

$(BUILD_OUT)/$(TOP).bit: $(BUILD_OUT)/impl/$(TOP).frames
	xc7frames2bit \
	    --part_file $(PRJXRAY_DB_DIR)/$(FAMILY)/$(PACKAGE)/part.yaml \
	    --part_name $(PACKAGE) \
	    --frm_file $< \
	    --output_file $@
endif

.PHONY: simulation
$(BUILD_OUT)/sim/$(TOP).vcd: $(BUILD_OUT)/synth/$(TOP).json
	rm -rf $(BUILD_OUT)/sim/*
	mkdir -p $(BUILD_OUT)/sim
	iverilog -D'DUMPFILE="$(BUILD_OUT)/sim/$(TOP).vcd"' -o $(BUILD_OUT)/sim/$(TOP).vvp $(PRJ_ROOT)/$(SRC_DIR)/$(TOP).v $(SRC_ROOT)/$(TOP)_tb.v $(CELLS_SYM)
	vvp -n $(BUILD_OUT)/sim/$(TOP).vvp