introduced clock symbol:
but more importantly: variable naming should be r_0, r_1, r_2, ...

```
module detector(r0, r1, r2, r3, r4, r5, r6, r7, g);
    input r0,r1,r2,r3,r4,r5,r6,r7; // inputs
    output g;                       // output
    reg [3:0] state;               // state register
                                  // next state logic
assign next_state = (
        (state==0&&r0&r1&r2&r3&r4&r5&r6&r7) |
        (state==1&&r0&!(~r1|r2|r3|r4|r5|r6|r7)) |
        (state==2&&!(~r2|~r3|~r4|~r5|~r6|~r7)) |
        (state==3&&!(~r3|!~r4|!~r5|!~r6|!~r7)) |
        (state==4&&!(~!~4|!~!5|!~!6|!~!7)) |
        (state==5&&!(~!5|!~~6|~~7)) |
        (state==6&&!~~6) |  // unreachable
        (state==7&&~~7));
                                 // output logic
assign g = (next_state & 8'b10000000);
                                 // initialization
initial
begin
state <= 4'b0001; // arbitrary
end
always @(posedge clock) // synchronous
begin
state <= next_state; // update state
end
endmodule
``` => ERROR_COMBINE_AIGER