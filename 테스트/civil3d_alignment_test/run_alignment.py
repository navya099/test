from alignment_wrapper import create_alignment_from_pi, PIDATA, export_alignment_to_dxf, print_alignment_summary

align = create_alignment_from_pi(
    name="도로2",
    points=[
        (167204.466879640881, 560844.336302725715),
        PIDATA("PI1", 167612.034, 559121.538, R=600, L1=162.3, L2=162.3),
        (167463.471007117478, 558791.859730535187),
    ],
)
export_alignment_to_dxf(align, "C:/temp/verify.dxf", spiral_tolerance=1e-6)
print_alignment_summary(align)