window.TIMELINE = {
 "total": 710.7,
 "scenes": [
  {
   "id": "intro",
   "title": "Welcome",
   "start": 0.0,
   "dur": 18.041,
   "cues": [
    {
     "id": "i1",
     "text": "Every time a computer adds two numbers, it uses a little circuit called a full adder. By the end of this video, you will build one with your own hands, on a breadboard, and you will know why every single wire is there.",
     "start": 0.9,
     "dur": 12.112,
     "speech": 11.562
    },
    {
     "id": "i2",
     "text": "You don't need any background. We start with adding numbers the way you did in school.",
     "start": 13.012,
     "dur": 5.03,
     "speech": 4.48
    }
   ]
  },
  {
   "id": "column",
   "title": "Adding one column",
   "start": 18.041,
   "dur": 43.861,
   "cues": [
    {
     "id": "c1",
     "text": "Let's add forty-seven plus thirty-eight, by hand. We work one column at a time, starting from the right.",
     "start": 0.9,
     "dur": 6.516,
     "speech": 5.966
    },
    {
     "id": "c2",
     "text": "Seven plus eight is fifteen. Fifteen doesn't fit in one column. So we write down the five, and carry the one to the next column.",
     "start": 7.416,
     "dur": 8.429,
     "speech": 7.879
    },
    {
     "id": "c3",
     "text": "Next column. Four plus three, plus the one we carried, makes eight. The answer is eighty-five.",
     "start": 15.845,
     "dur": 6.398,
     "speech": 5.848
    },
    {
     "id": "c4",
     "text": "Now notice what each column really does. It takes in three things: a digit from the top number, a digit from the bottom number, and a carry coming in from the right. And it gives out two things: a digit to write down, and a carry to pass on to the left.",
     "start": 22.243,
     "dur": 15,
     "speech": 13.719
    },
    {
     "id": "c5",
     "text": "Hold on to that picture. Three things in, two things out. That is exactly what a full adder is.",
     "start": 37.243,
     "dur": 6.618,
     "speech": 6.068
    }
   ]
  },
  {
   "id": "binary",
   "title": "Only zeros and ones",
   "start": 61.902,
   "dur": 38.608,
   "cues": [
    {
     "id": "b1",
     "text": "Computers don't have ten digits. They only have two: zero and one. Off and on. A switch that is down, or a switch that is up.",
     "start": 0.9,
     "dur": 9.496,
     "speech": 8.946
    },
    {
     "id": "b2",
     "text": "So adding one column in binary is very simple. Zero plus zero is zero. Zero plus one is one.",
     "start": 10.396,
     "dur": 7.466,
     "speech": 6.916
    },
    {
     "id": "b3",
     "text": "But one plus one is two, and there is no digit two. Two in binary is written one, zero. So we write down a zero, and carry a one. It's just like fifteen in decimal: write the five, carry the one.",
     "start": 17.862,
     "dur": 12.816,
     "speech": 12.266
    },
    {
     "id": "b4",
     "text": "And if a carry is also coming in, one plus one plus one is three. Three in binary is one, one. Write down a one, and carry a one.",
     "start": 30.678,
     "dur": 7.93,
     "speech": 7.38
    }
   ]
  },
  {
   "id": "count",
   "title": "The big idea: count the ones",
   "start": 100.51,
   "dur": 63.663,
   "cues": [
    {
     "id": "k1",
     "text": "Here is our full adder as a closed box. Three inputs on the left: A, B, and Carry in. Two output lights on the right: Carry out, and Sum.",
     "start": 0.9,
     "dur": 9.59,
     "speech": 9.04
    },
    {
     "id": "k2",
     "text": "And here is the secret that makes it easy. A full adder simply counts how many of its three inputs are switched on. Zero, one, two, or three. Then it shows that count in binary, on its two lights.",
     "start": 10.49,
     "dur": 12.503,
     "speech": 11.953
    },
    {
     "id": "k3",
     "text": "Count zero: both lights off. Count one: only the Sum light. Count two: only the Carry light, because two is one, zero. Count three: both lights, because three is one, one.",
     "start": 22.993,
     "dur": 14,
     "speech": 11.779
    },
    {
     "id": "k4",
     "text": "Here are all eight ways to set three switches. Next to each, the count, and the two lights. Look at the pattern.",
     "start": 36.993,
     "dur": 6.665,
     "speech": 6.115
    },
    {
     "id": "k5",
     "text": "The Sum light is on whenever the count is odd: one, or three. The Carry light is on whenever two or more inputs are on.",
     "start": 43.658,
     "dur": 9,
     "speech": 7.092
    },
    {
     "id": "k6",
     "text": "That is the whole full adder. Sum means: an odd number of ones. Carry means: two or more ones. Everything else is just building those two ideas out of parts.",
     "start": 52.658,
     "dur": 11.005,
     "speech": 10.455
    }
   ]
  },
  {
   "id": "gates",
   "title": "Logic gates: tiny judges",
   "start": 164.173,
   "dur": 54.94,
   "cues": [
    {
     "id": "g1",
     "text": "Our parts are called logic gates. Each gate looks at two inputs, and decides whether to turn its output on. Think of each one as a tiny judge with exactly one rule.",
     "start": 0.9,
     "dur": 10.496,
     "speech": 9.946
    },
    {
     "id": "g2",
     "text": "The AND gate's rule: on, only if both inputs are on. Like a lamp wired through two switches in a row. You need both of them closed.",
     "start": 11.396,
     "dur": 10,
     "speech": 7.705
    },
    {
     "id": "g3",
     "text": "The OR gate's rule: on, if either input is on, or both. Like two switches side by side. Either one can light the lamp.",
     "start": 21.396,
     "dur": 10,
     "speech": 7.578
    },
    {
     "id": "g4",
     "text": "The XOR gate, short for exclusive or, has the most interesting rule: on, only if the two inputs are different. One on, one off. If both are on, it says no. Another way to say it: XOR is on when the number of ones is odd.",
     "start": 31.396,
     "dur": 15.823,
     "speech": 15.273
    },
    {
     "id": "g5",
     "text": "That last sentence is the key. XOR is an odd detector. And our Sum light is exactly an odd detector.",
     "start": 47.219,
     "dur": 7.721,
     "speech": 7.171
    }
   ]
  },
  {
   "id": "sum",
   "title": "Building the Sum",
   "start": 219.114,
   "dur": 34.103,
   "cues": [
    {
     "id": "s1",
     "text": "So let's build the Sum. First, we XOR A with B. Its output answers one question: counting only A and B, is the number of ones odd?",
     "start": 0.9,
     "dur": 9.66,
     "speech": 9.11
    },
    {
     "id": "s2",
     "text": "Then we XOR that answer with Carry in. If Carry in is off, the answer stays the same. If Carry in is on, it flips: odd becomes even, even becomes odd.",
     "start": 10.56,
     "dur": 10.542,
     "speech": 9.992
    },
    {
     "id": "s3",
     "text": "So the final output is on exactly when the total count is odd. That is the Sum. Two XOR gates in a chain. Watch a few examples.",
     "start": 21.103,
     "dur": 13,
     "speech": 8.191
    }
   ]
  },
  {
   "id": "carry",
   "title": "Building the Carry",
   "start": 253.216,
   "dur": 42.018,
   "cues": [
    {
     "id": "r1",
     "text": "Now the Carry out. It must turn on when two or more inputs are on. There are only two ways that can happen.",
     "start": 0.9,
     "dur": 6.874,
     "speech": 6.324
    },
    {
     "id": "r2",
     "text": "Way one: A and B are both on. That's simply an AND gate on A and B.",
     "start": 7.774,
     "dur": 5.25,
     "speech": 4.7
    },
    {
     "id": "r3",
     "text": "Way two: exactly one of A or B is on, and Carry in is on too. But 'exactly one of A or B' is what our first XOR gate already tells us. So we reuse it: a second AND gate, on the XOR output and Carry in.",
     "start": 13.024,
     "dur": 14.188,
     "speech": 13.638
    },
    {
     "id": "r4",
     "text": "If either way is true, we carry. Either, means an OR gate. So Carry out is the OR of our two AND gates.",
     "start": 27.212,
     "dur": 7.501,
     "speech": 6.951
    },
    {
     "id": "r5",
     "text": "Reusing that XOR output is a neat trick. It saves parts, and it's the standard design you will see in every textbook.",
     "start": 34.713,
     "dur": 7.305,
     "speech": 6.755
    }
   ]
  },
  {
   "id": "circuit",
   "title": "The complete circuit",
   "start": 295.234,
   "dur": 48.449,
   "cues": [
    {
     "id": "f1",
     "text": "Here's the complete full adder. Two XOR gates, two AND gates, and one OR gate. Five gates. Let's try every possible input, and watch the signals flow. Bright wires carry a one.",
     "start": 0.9,
     "dur": 12.977,
     "speech": 12.427
    },
    {
     "id": "f2",
     "text": "All off. Count zero. Nothing lights.",
     "start": 13.877,
     "dur": 4,
     "speech": 2.841
    },
    {
     "id": "f3",
     "text": "Only Carry in. Count one, odd. Sum lights.",
     "start": 17.877,
     "dur": 4.145,
     "speech": 3.595
    },
    {
     "id": "f4",
     "text": "Only B. Count one. Sum.",
     "start": 22.022,
     "dur": 4,
     "speech": 2.04
    },
    {
     "id": "f5",
     "text": "B and Carry in. Count two. Carry lights, Sum is off.",
     "start": 26.022,
     "dur": 4.32,
     "speech": 3.77
    },
    {
     "id": "f6",
     "text": "Only A. Count one. Sum.",
     "start": 30.342,
     "dur": 4,
     "speech": 1.831
    },
    {
     "id": "f7",
     "text": "A and Carry in. Count two. Carry.",
     "start": 34.342,
     "dur": 4,
     "speech": 2.957
    },
    {
     "id": "f8",
     "text": "A and B. Count two. Carry. This one goes through the first AND gate.",
     "start": 38.342,
     "dur": 5.107,
     "speech": 4.557
    },
    {
     "id": "f9",
     "text": "All three. Count three. Both lights. One, one.",
     "start": 43.449,
     "dur": 5,
     "speech": 3.802
    }
   ]
  },
  {
   "id": "kit",
   "title": "Meet your trainer kit",
   "start": 343.683,
   "dur": 37.792,
   "cues": [
    {
     "id": "t1",
     "text": "Now, the real thing. Your trainer kit has everything built in. Let's find the parts we'll use.",
     "start": 0.9,
     "dur": 6.351,
     "speech": 5.801
    },
    {
     "id": "t2",
     "text": "The power section has a plus five volt socket, often labelled V C C, and a ground socket, labelled G N D. Five volts means one. Ground, zero volts, means zero.",
     "start": 7.251,
     "dur": 11.982,
     "speech": 11.432
    },
    {
     "id": "t3",
     "text": "The logic switches. Each switch outputs five volts when it's up, and zero volts when it's down. Three of them will be A, B, and Carry in.",
     "start": 19.233,
     "dur": 8.522,
     "speech": 7.972
    },
    {
     "id": "t4",
     "text": "The LEDs. Each one lights up when its input gets five volts. Two of them will show Carry out and Sum.",
     "start": 27.756,
     "dur": 6.746,
     "speech": 6.196
    },
    {
     "id": "t5",
     "text": "And in the middle, the breadboard, where the chips will go.",
     "start": 34.502,
     "dur": 3.29,
     "speech": 2.74
    }
   ]
  },
  {
   "id": "breadboard",
   "title": "How a breadboard connects",
   "start": 381.475,
   "dur": 42.061,
   "cues": [
    {
     "id": "d1",
     "text": "A breadboard looks like a field of holes. But underneath, the holes are joined in a simple pattern.",
     "start": 0.9,
     "dur": 5.993,
     "speech": 5.443
    },
    {
     "id": "d2",
     "text": "In the middle area, each short strip of five holes is joined by a metal clip. Anything plugged into the same strip of five is connected together.",
     "start": 6.893,
     "dur": 9,
     "speech": 8.392
    },
    {
     "id": "d3",
     "text": "The groove down the center splits every strip into two separate halves. Chips sit across this groove, so each leg of the chip gets its own strip.",
     "start": 15.893,
     "dur": 9,
     "speech": 7.881
    },
    {
     "id": "d4",
     "text": "Along the edges are the long power rails. Every hole along a rail is connected. We'll put five volts on a red rail and ground on a blue rail, so every chip can reach power easily. On some boards the rails are split in the middle. If yours are, bridge the gap with a short wire.",
     "start": 24.893,
     "dur": 17.168,
     "speech": 16.618
    }
   ]
  },
  {
   "id": "chips",
   "title": "The three chips",
   "start": 423.536,
   "dur": 56.818,
   "cues": [
    {
     "id": "p1",
     "text": "We need three chips. The seventy four eighty six holds four XOR gates. The seventy four oh eight holds four AND gates. The seventy four thirty two holds four OR gates. You may see them labelled 74 L S, or 74 H C. Either works.",
     "start": 0.9,
     "dur": 16.168,
     "speech": 15.618
    },
    {
     "id": "p2",
     "text": "Find the notch, or the dot, at one end of the chip. With the notch on the left, pin one is at the bottom left. Pins count along the bottom to pin seven, then turn the corner, and come back along the top, right to left, up to pin fourteen.",
     "start": 17.068,
     "dur": 15,
     "speech": 14.033
    },
    {
     "id": "p3",
     "text": "Pin fourteen is power, V C C. Pin seven is ground. Every chip needs both, or it does nothing at all.",
     "start": 32.068,
     "dur": 7.698,
     "speech": 7.148
    },
    {
     "id": "p4",
     "text": "And here is a lucky break. All three chips share the same pin layout. Gate one: inputs on pins one and two, output on pin three. Gate two: inputs on pins four and five, output on pin six. We only need gates one and two on each chip.",
     "start": 39.766,
     "dur": 17.052,
     "speech": 16.502
    }
   ]
  },
  {
   "id": "build",
   "title": "Build it, step by step",
   "start": 480.354,
   "dur": 109.092,
   "cues": [
    {
     "id": "w1",
     "text": "Step one. With the kit switched off, push the three chips across the center groove, all notches facing left. From left to right: the XOR chip, the AND chip, then the OR chip. Leave some space between them.",
     "start": 0.9,
     "dur": 14.082,
     "speech": 13.532
    },
    {
     "id": "w2",
     "text": "Step two: power. Connect the kit's plus five volt socket to the red rail, and ground to the blue rail. Then, for every chip, a red wire from pin fourteen to the red rail, and a black wire from pin seven to the blue rail.",
     "start": 14.982,
     "dur": 14,
     "speech": 13.116
    },
    {
     "id": "w3",
     "text": "Step three: inputs A and B. Wire switch one, that's A, to XOR pin one. Wire switch two, that's B, to XOR pin two.",
     "start": 28.982,
     "dur": 9.753,
     "speech": 9.203
    },
    {
     "id": "w4",
     "text": "A and B also feed the first AND gate. So add two jumpers: from the XOR pin one strip to AND pin one, and from the XOR pin two strip to AND pin two. Remember: any hole in the same strip is the same connection.",
     "start": 38.735,
     "dur": 14.989,
     "speech": 14.439
    },
    {
     "id": "w5",
     "text": "Step four: the Sum chain. A short jumper from XOR pin three to XOR pin four. Then wire switch three, Carry in, to XOR pin five. XOR pin six is now the Sum.",
     "start": 53.724,
     "dur": 12.329,
     "speech": 11.779
    },
    {
     "id": "w6",
     "text": "Step five: the second AND gate. Wire XOR pin three to AND pin four. And wire Carry in, from the XOR pin five strip, to AND pin five.",
     "start": 66.052,
     "dur": 10.194,
     "speech": 9.644
    },
    {
     "id": "w7",
     "text": "Step six: the OR gate. Wire AND pin three to OR pin one, and AND pin six to OR pin two. OR pin three is now the Carry out.",
     "start": 76.246,
     "dur": 10,
     "speech": 9.04
    },
    {
     "id": "w8",
     "text": "Step seven: the lights. Choose two LEDs next to each other. Wire OR pin three to the left one: that's Carry out. Wire XOR pin six to the right one: that's Sum. Now the two lights read like a binary number.",
     "start": 86.246,
     "dur": 14.149,
     "speech": 13.599
    },
    {
     "id": "w9",
     "text": "That's every wire. Twenty in total: eight for power, and twelve for signals. Before switching on, check each one against the list.",
     "start": 100.396,
     "dur": 8.696,
     "speech": 8.146
    }
   ]
  },
  {
   "id": "test",
   "title": "Power on and test",
   "start": 589.446,
   "dur": 41.557,
   "cues": [
    {
     "id": "x1",
     "text": "Switch the kit on, and test all eight combinations. Before each flip, predict the lights with the count rule. Odd count: Sum. Two or more: Carry.",
     "start": 0.9,
     "dur": 10.657,
     "speech": 10.107
    },
    {
     "id": "x2",
     "text": "Watch the glowing wires. They carry five volts, a one. Follow any bright path, and you can see each gate making its decision.",
     "start": 11.557,
     "dur": 30,
     "speech": 7.102
    }
   ]
  },
  {
   "id": "debug",
   "title": "If it doesn't work",
   "start": 631.003,
   "dur": 46.637,
   "cues": [
    {
     "id": "e1",
     "text": "If something is wrong, don't worry. Check these in order.",
     "start": 0.9,
     "dur": 3.787,
     "speech": 3.237
    },
    {
     "id": "e2",
     "text": "Nothing lights at all? Check that every chip has its power wires on pin fourteen and pin seven, that the rails are bridged, and that the kit is on.",
     "start": 4.687,
     "dur": 8.513,
     "speech": 7.963
    },
    {
     "id": "e3",
     "text": "A chip gets hot? It's probably in backwards. Switch off right away, and check the notch.",
     "start": 13.2,
     "dur": 6.502,
     "speech": 5.952
    },
    {
     "id": "e4",
     "text": "Sum is right but Carry is wrong, or the other way round? Test one gate at a time. Move an LED wire onto a gate's output, pin three or pin six, and check it against that gate's rule.",
     "start": 19.702,
     "dur": 11.378,
     "speech": 10.828
    },
    {
     "id": "e5",
     "text": "An output stuck on? An input that isn't connected to anything acts like a one on L S chips. Look for a wire in the wrong strip. And if you use H C chips, tie the unused inputs, pins nine, ten, twelve and thirteen, to ground.",
     "start": 31.08,
     "dur": 15.556,
     "speech": 15.006
    }
   ]
  },
  {
   "id": "recap",
   "title": "Recap",
   "start": 677.639,
   "dur": 31.56,
   "cues": [
    {
     "id": "z1",
     "text": "Let's recap. A full adder adds one column of binary: A, B, and a carry coming in.",
     "start": 0.9,
     "dur": 6.26,
     "speech": 5.71
    },
    {
     "id": "z2",
     "text": "It counts the ones. Sum is on when the count is odd: two XOR gates. Carry is on when the count is two or more: A AND B, or Carry in AND the XOR, joined by an OR.",
     "start": 7.16,
     "dur": 12.4,
     "speech": 11.85
    },
    {
     "id": "z3",
     "text": "Chain four of them, each Carry out feeding the next Carry in, and you can add two four bit numbers. That's how real computers add. And you just built the first column yourself.",
     "start": 19.56,
     "dur": 12,
     "speech": 10.039
    }
   ]
  }
 ]
};
