//////////////////////////////////////////////////////////////////////////////////
// Company:         University of Duisburg-Essen, Intelligent Embedded Systems Lab
// Engineer:        AE
//
// Create Date:     11.06.2026, 22:04,43
// Copied on: 	    {$date_copy_created}
// Module Name:     SKELETON_MATH_MULT
// Target Devices:  FPGA
// Tool Versions:   1v1
// Description:     Skeleton for testing simple math operations on device (MULT, ADDER)
// Dependencies:    None
//
// State: 	        Works! (System Test done: 16.01.2025)
// Improvements:    None
// Parameters:      BITWIDTH_IN 	--> Bitwidth of input data
//                  BITWIDTH_SYS 	--> Bitwidth of data bus on device
//                  BITWIDTH_ADR    --> Bitwidth of address range
//                  BITWIDTH_HEAD	--> Bitwidth of metadata (skeleton properties)
//////////////////////////////////////////////////////////////////////////////////


module SKELETON_MATH_MULT#(
    parameter integer BITWIDTH_IN = 8,
    parameter integer BITWIDTH_SYS = 16,
    parameter integer BITWIDTH_HEAD = 26,
    parameter integer BITWIDTH_ADR = 6,
    parameter integer NUM_PARAMS = 1,
    parameter integer NUM_MULT = 1
)(
    input wire CLK_SYS,
    input wire RSTN,
    input wire EN,
    input wire TRGG_START_CALC,
    input wire RnW,
    input wire [BITWIDTH_ADR-'d1:0] ADR,
    input wire [BITWIDTH_SYS-'d1:0] DATA_IN,
    output wire [BITWIDTH_SYS-'d1:0] DATA_OUT,
    output wire [BITWIDTH_HEAD-'d1:0] DATA_HEAD,
    output wire RDY
);

localparam WAIT_CYC_MULT = 8'd1;
localparam BITWIDTH_OFFSET = BITWIDTH_SYS - BITWIDTH_IN;
localparam BITWIDTH_OUT = 2*BITWIDTH_IN;
localparam SIZE_INPUT = NUM_PARAMS, SIZE_OUTPUT = 1;

assign DATA_HEAD = {4'd4, SIZE_INPUT[5:0], SIZE_OUTPUT[5:0], BITWIDTH_IN[4:0], BITWIDTH_OUT[4:0]};

// --- Control lines
reg run_test;
reg [$clog2(WAIT_CYC_MULT):0] cnt_mult_wait;

reg [BITWIDTH_IN-'d1:0] data_dut [SIZE_INPUT-'d1:0];

reg [SIZE_OUTPUT*BITWIDTH_OUT-'d1:0] pipe_dut_out;
wire signed [SIZE_OUTPUT*BITWIDTH_OUT-'d1:0] data_mul;
assign RDY = ~run_test;

// --- Converting data
if((BITWIDTH_SYS-BITWIDTH_OUT) > 0) begin
    assign DATA_OUT = {pipe_dut_out[0+:BITWIDTH_OUT], {(BITWIDTH_SYS-BITWIDTH_OUT){1'd0}}};
end else begin
    assign DATA_OUT = pipe_dut_out[0+:BITWIDTH_OUT];
end

// --- Testing routine
integer i0;
always@(posedge CLK_SYS) begin
    if(!(RSTN && EN)) begin
        run_test <= 1'd0;
        cnt_mult_wait <= 'd0;
        pipe_dut_out <= 'd0;
        for(i0 = 'd0; i0 < SIZE_INPUT; i0 = i0 + 'd1) begin
            data_dut[i0] <= 'd0;
        end
    end else begin
        // --- Loading data to internal RAM
        data_dut[ADR] <= (!RnW) ? DATA_IN[(BITWIDTH_SYS-'d1)-:BITWIDTH_IN] : data_dut[ADR];

        // --- Pipelining Multiplier Input (1-Delay Stage)
        if(run_test && |DATA_IN[0+:(BITWIDTH_SYS-BITWIDTH_IN)]) begin
            run_test <= (cnt_mult_wait == WAIT_CYC_MULT) ? 1'd0 : run_test;
            cnt_mult_wait <= (cnt_mult_wait == WAIT_CYC_MULT) ? 'd0 : cnt_mult_wait + 'd1;
            pipe_dut_out <= data_mul;
        end else begin
            run_test <= TRGG_START_CALC;
            cnt_mult_wait <= 'd0;
            pipe_dut_out <= pipe_dut_out;
        end
    end
end

// --- DUT (JUST REPLACE HERE)
MULT_SIGNED#(
    .BITWIDTH(BITWIDTH_IN)
) MULT (
    .A(data_dut[0]),
    .B(data_dut[1]),
    .Q(data_mul)
);

endmodule
