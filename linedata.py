from facility.platform import Platform
from tr.linesegment import LineSegment


"""
a simple metro line data:
============================>
d1-s11-s12-s13-s14-s15-s16-d2
 |-s21-s22-s23-s24-s25-s26-|
<===========================
d1:1
s11:2
s12:3
s13:4
s14:5
s15:6
s16:7
d2:8
s21:9
s22:10
s23:11
s24:12
s25:13
s26:14
"""

# Create platform objects
d1 = Platform(1, "d1", 120)
s11 = Platform(2, "s11")
s12 = Platform(3, "s12")
s13 = Platform(4, "s13")
s14 = Platform(5, "s14")
s15 = Platform(6, "s15")
s16 = Platform(7, "s16")
d2 = Platform(8, "d2", 120)
s21 = Platform(9, "s21")
s22 = Platform(10, "s22")
s23 = Platform(11, "s23")
s24 = Platform(12, "s24")
s25 = Platform(13, "s25")
s26 = Platform(14, "s26")

# Create line segment objects
line_segments = [
    LineSegment(d1, s11),
    LineSegment(s11, s12),
    LineSegment(s12, s13),
    LineSegment(s13, s14),
    LineSegment(s14, s15),
    LineSegment(s15, s16),
    LineSegment(s16, d2),
    LineSegment(d2, s26),
    LineSegment(s26, s25),
    LineSegment(s25, s24),
    LineSegment(s24, s23),
    LineSegment(s23, s22),
    LineSegment(s22, s21),
    LineSegment(s21, d1)
]

platforms = [d1, s11, s12, s13, s14, s15, s16, d2, s21, s22, s23, s24, s25, s26]

if __name__ == "__main__":
    # Print the created platforms and line segments
    for platform in platforms:
        print(platform)

    for segment in line_segments:
        print(segment)