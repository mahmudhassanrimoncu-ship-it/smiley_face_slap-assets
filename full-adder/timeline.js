window.TIMELINE = {
 "total": 742.609,
 "scenes": [
  {
   "id": "intro",
   "title": "Welcome",
   "start": 0.0,
   "dur": 20.096,
   "cues": [
    {
     "id": "i1",
     "text": "Every time a computer adds two numbers, it uses a little circuit called a full adder. By the end of this video, you will build one with your own hands, on a breadboard, and you will know why every single wire is there.",
     "start": 0.9,
     "dur": 13.818,
     "speech": 13.268
    },
    {
     "id": "i2",
     "text": "You don't need any background. We start with adding numbers the way you did in school.",
     "start": 14.718,
     "dur": 5.378,
     "speech": 4.828
    }
   ]
  },
  {
   "id": "column",
   "title": "Adding one column",
   "start": 20.096,
   "dur": 45.905,
   "cues": [
    {
     "id": "c1",
     "text": "Let's add forty-seven plus thirty-eight, by hand. We work one column at a time, starting from the right.",
     "start": 0.9,
     "dur": 6.957,
     "speech": 6.407
    },
    {
     "id": "c2",
     "text": "Seven plus eight is fifteen. Fifteen doesn't fit in one column. So we write down the five, and carry the one to the next column.",
     "start": 7.857,
     "dur": 8.406,
     "speech": 7.856
    },
    {
     "id": "c3",
     "text": "Next column. Four plus three, plus the one we carried, makes eight. The answer is eighty-five.",
     "start": 16.263,
     "dur": 7.001,
     "speech": 6.451
    },
    {
     "id": "c4",
     "text": "Now notice what each column really does. It takes in three things: a digit from the top number, a digit from the bottom number, and a carry coming in from the right. And it gives out two things: a digit to write down, and a carry to pass on to the left.",
     "start": 23.265,
     "dur": 15.337,
     "speech": 14.787
    },
    {
     "id": "c5",
     "text": "Hold on to that picture. Three things in, two things out. That is exactly what a full adder is.",
     "start": 38.602,
     "dur": 7.303,
     "speech": 6.753
    }
   ]
  },
  {
   "id": "binary",
   "title": "Only zeros and ones",
   "start": 66.001,
   "dur": 41.986,
   "cues": [
    {
     "id": "b1",
     "text": "Computers don't have ten digits. They only have two: zero and one. Off and on. A switch that is down, or a switch that is up.",
     "start": 0.9,
     "dur": 10.03,
     "speech": 9.48
    },
    {
     "id": "b2",
     "text": "So adding one column in binary is very simple. Zero plus zero is zero. Zero plus one is one.",
     "start": 10.93,
     "dur": 7.559,
     "speech": 7.009
    },
    {
     "id": "b3",
     "text": "But one plus one is two, and there is no digit two. Two in binary is written one, zero. So we write down a zero, and carry a one. It's just like fifteen in decimal: write the five, carry the one.",
     "start": 18.488,
     "dur": 13.989,
     "speech": 13.439
    },
    {
     "id": "b4",
     "text": "And if a carry is also coming in, one plus one plus one is three. Three in binary is one, one. Write down a one, and carry a one.",
     "start": 32.477,
     "dur": 9.509,
     "speech": 8.959
    }
   ]
  },
  {
   "id": "count",
   "title": "The big idea: count the ones",
   "start": 107.988,
   "dur": 67.181,
   "cues": [
    {
     "id": "k1",
     "text": "Here is our full adder as a closed box. Three inputs on the left: A, B, and Carry in. Two output lights on the right: Carry out, and Sum.",
     "start": 0.9,
     "dur": 10.624,
     "speech": 10.074
    },
    {
     "id": "k2",
     "text": "And here is the secret that makes it easy. A full adder simply counts how many of its three inputs are switched on. Zero, one, two, or three. Then it shows that count in binary, on its two lights.",
     "start": 11.524,
     "dur": 13.536,
     "speech": 12.986
    },
    {
     "id": "k3",
     "text": "Count zero: both lights off. Count one: only the Sum light. Count two: only the Carry light, because two is one, zero. Count three: both lights, because three is one, one.",
     "start": 25.06,
     "dur": 14,
     "speech": 12.847
    },
    {
     "id": "k4",
     "text": "Here are all eight ways to set three switches. Next to each, the count, and the two lights. Look at the pattern.",
     "start": 39.06,
     "dur": 7.686,
     "speech": 7.136
    },
    {
     "id": "k5",
     "text": "The Sum light is on whenever the count is odd: one, or three. The Carry light is on whenever two or more inputs are on.",
     "start": 46.746,
     "dur": 9,
     "speech": 7.301
    },
    {
     "id": "k6",
     "text": "That is the whole full adder. Sum means: an odd number of ones. Carry means: two or more ones. Everything else is just building those two ideas out of parts.",
     "start": 55.746,
     "dur": 11.435,
     "speech": 10.885
    }
   ]
  },
  {
   "id": "gates",
   "title": "Logic gates: tiny judges",
   "start": 175.169,
   "dur": 55.997,
   "cues": [
    {
     "id": "g1",
     "text": "Our parts are called logic gates. Each gate looks at two inputs, and decides whether to turn its output on. Think of each one as a tiny judge with exactly one rule.",
     "start": 0.9,
     "dur": 10.868,
     "speech": 10.318
    },
    {
     "id": "g2",
     "text": "The AND gate's rule: on, only if both inputs are on. Like a lamp wired through two switches in a row. You need both of them closed.",
     "start": 11.768,
     "dur": 10,
     "speech": 9.04
    },
    {
     "id": "g3",
     "text": "The OR gate's rule: on, if either input is on, or both. Like two switches side by side. Either one can light the lamp.",
     "start": 21.768,
     "dur": 10,
     "speech": 8.1
    },
    {
     "id": "g4",
     "text": "The XOR gate, short for exclusive or, has the most interesting rule: on, only if the two inputs are different. One on, one off. If both are on, it says no. Another way to say it: XOR is on when the number of ones is odd.",
     "start": 31.768,
     "dur": 16.218,
     "speech": 15.668
    },
    {
     "id": "g5",
     "text": "That last sentence is the key. XOR is an odd detector. And our Sum light is exactly an odd detector.",
     "start": 47.985,
     "dur": 8.011,
     "speech": 7.461
    }
   ]
  },
  {
   "id": "sum",
   "title": "Building the Sum",
   "start": 231.166,
   "dur": 36.076,
   "cues": [
    {
     "id": "s1",
     "text": "So let's build the Sum. First, we XOR A with B. Its output answers one question: counting only A and B, is the number of ones odd?",
     "start": 0.9,
     "dur": 10.217,
     "speech": 9.667
    },
    {
     "id": "s2",
     "text": "Then we XOR that answer with Carry in. If Carry in is off, the answer stays the same. If Carry in is on, it flips: odd becomes even, even becomes odd.",
     "start": 11.117,
     "dur": 11.959,
     "speech": 11.409
    },
    {
     "id": "s3",
     "text": "So the final output is on exactly when the total count is odd. That is the Sum. Two XOR gates in a chain. Watch a few examples.",
     "start": 23.076,
     "dur": 13,
     "speech": 9.584
    }
   ]
  },
  {
   "id": "carry",
   "title": "Building the Carry",
   "start": 267.242,
   "dur": 44.351,
   "cues": [
    {
     "id": "r1",
     "text": "Now the Carry out. It must turn on when two or more inputs are on. There are only two ways that can happen.",
     "start": 0.9,
     "dur": 7.535,
     "speech": 6.985
    },
    {
     "id": "r2",
     "text": "Way one: A and B are both on. That's simply an AND gate on A and B.",
     "start": 8.435,
     "dur": 5.482,
     "speech": 4.932
    },
    {
     "id": "r3",
     "text": "Way two: exactly one of A or B is on, and Carry in is on too. But 'exactly one of A or B' is what our first XOR gate already tells us. So we reuse it: a second AND gate, on the XOR output and Carry in.",
     "start": 13.918,
     "dur": 14.827,
     "speech": 14.277
    },
    {
     "id": "r4",
     "text": "If either way is true, we carry. Either, means an OR gate. So Carry out is the OR of our two AND gates.",
     "start": 28.744,
     "dur": 7.826,
     "speech": 7.276
    },
    {
     "id": "r5",
     "text": "Reusing that XOR output is a neat trick. It saves parts, and it's the standard design you will see in every textbook.",
     "start": 36.57,
     "dur": 7.781,
     "speech": 7.231
    }
   ]
  },
  {
   "id": "circuit",
   "title": "The complete circuit",
   "start": 311.593,
   "dur": 50.878,
   "cues": [
    {
     "id": "f1",
     "text": "Here's the complete full adder. Two XOR gates, two AND gates, and one OR gate. Five gates. Let's try every possible input, and watch the signals flow. Bright wires carry a one.",
     "start": 0.9,
     "dur": 13.697,
     "speech": 13.147
    },
    {
     "id": "f2",
     "text": "All off. Count zero. Nothing lights.",
     "start": 14.597,
     "dur": 4,
     "speech": 3.352
    },
    {
     "id": "f3",
     "text": "Only Carry in. Count one, odd. Sum lights.",
     "start": 18.597,
     "dur": 4.203,
     "speech": 3.653
    },
    {
     "id": "f4",
     "text": "Only B. Count one. Sum.",
     "start": 22.8,
     "dur": 4,
     "speech": 2.829
    },
    {
     "id": "f5",
     "text": "B and Carry in. Count two. Carry lights, Sum is off.",
     "start": 26.8,
     "dur": 5.097,
     "speech": 4.547
    },
    {
     "id": "f6",
     "text": "Only A. Count one. Sum.",
     "start": 31.897,
     "dur": 4,
     "speech": 3.166
    },
    {
     "id": "f7",
     "text": "A and Carry in. Count two. Carry.",
     "start": 35.897,
     "dur": 4,
     "speech": 3.177
    },
    {
     "id": "f8",
     "text": "A and B. Count two. Carry. This one goes through the first AND gate.",
     "start": 39.897,
     "dur": 5.804,
     "speech": 5.254
    },
    {
     "id": "f9",
     "text": "All three. Count three. Both lights. One, one.",
     "start": 45.701,
     "dur": 5.177,
     "speech": 4.627
    }
   ]
  },
  {
   "id": "kit",
   "title": "Meet your trainer kit",
   "start": 362.471,
   "dur": 41.611,
   "cues": [
    {
     "id": "t1",
     "text": "Now, the real thing. Your trainer kit has everything built in. Let's find the parts we'll use.",
     "start": 0.9,
     "dur": 7.176,
     "speech": 6.626
    },
    {
     "id": "t2",
     "text": "The power section has a plus five volt socket, often labelled V C C, and a ground socket, labelled G N D. Five volts means one. Ground, zero volts, means zero.",
     "start": 8.076,
     "dur": 12.168,
     "speech": 11.618
    },
    {
     "id": "t3",
     "text": "The logic switches. Each switch outputs five volts when it's up, and zero volts when it's down. Three of them will be A, B, and Carry in.",
     "start": 20.243,
     "dur": 9.788,
     "speech": 9.238
    },
    {
     "id": "t4",
     "text": "The LEDs. Each one lights up when its input gets five volts. Two of them will show Carry out and Sum.",
     "start": 30.031,
     "dur": 7.512,
     "speech": 6.962
    },
    {
     "id": "t5",
     "text": "And in the middle, the breadboard, where the chips will go.",
     "start": 37.544,
     "dur": 4.068,
     "speech": 3.518
    }
   ]
  },
  {
   "id": "breadboard",
   "title": "How a breadboard connects",
   "start": 404.083,
   "dur": 43.721,
   "cues": [
    {
     "id": "d1",
     "text": "A breadboard looks like a field of holes. But underneath, the holes are joined in a simple pattern.",
     "start": 0.9,
     "dur": 6.701,
     "speech": 6.151
    },
    {
     "id": "d2",
     "text": "In the middle area, each short strip of five holes is joined by a metal clip. Anything plugged into the same strip of five is connected together.",
     "start": 7.601,
     "dur": 9,
     "speech": 8.322
    },
    {
     "id": "d3",
     "text": "The groove down the center splits every strip into two separate halves. Chips sit across this groove, so each leg of the chip gets its own strip.",
     "start": 16.601,
     "dur": 9,
     "speech": 7.881
    },
    {
     "id": "d4",
     "text": "Along the edges are the long power rails. Every hole along a rail is connected. We'll put five volts on a red rail and ground on a blue rail, so every chip can reach power easily. On some boards the rails are split in the middle. If yours are, bridge the gap with a short wire.",
     "start": 25.601,
     "dur": 18.12,
     "speech": 17.57
    }
   ]
  },
  {
   "id": "chips",
   "title": "The three chips",
   "start": 447.804,
   "dur": 58.408,
   "cues": [
    {
     "id": "p1",
     "text": "We need three chips. The seventy four eighty six holds four XOR gates. The seventy four oh eight holds four AND gates. The seventy four thirty two holds four OR gates. You may see them labelled 74 L S, or 74 H C. Either works.",
     "start": 0.9,
     "dur": 16.771,
     "speech": 16.221
    },
    {
     "id": "p2",
     "text": "Find the notch, or the dot, at one end of the chip. With the notch on the left, pin one is at the bottom left. Pins count along the bottom to pin seven, then turn the corner, and come back along the top, right to left, up to pin fourteen.",
     "start": 17.671,
     "dur": 15,
     "speech": 14.068
    },
    {
     "id": "p3",
     "text": "Pin fourteen is power, V C C. Pin seven is ground. Every chip needs both, or it does nothing at all.",
     "start": 32.671,
     "dur": 8.279,
     "speech": 7.729
    },
    {
     "id": "p4",
     "text": "And here is a lucky break. All three chips share the same pin layout. Gate one: inputs on pins one and two, output on pin three. Gate two: inputs on pins four and five, output on pin six. We only need gates one and two on each chip.",
     "start": 40.95,
     "dur": 17.458,
     "speech": 16.908
    }
   ]
  },
  {
   "id": "build",
   "title": "Build it, step by step",
   "start": 506.212,
   "dur": 112.578,
   "cues": [
    {
     "id": "w1",
     "text": "Step one. With the kit switched off, push the three chips across the center groove, all notches facing left. From left to right: the XOR chip, the AND chip, then the OR chip. Leave some space between them.",
     "start": 0.9,
     "dur": 14.442,
     "speech": 13.892
    },
    {
     "id": "w2",
     "text": "Step two: power. Connect the kit's plus five volt socket to the red rail, and ground to the blue rail. Then, for every chip, a red wire from pin fourteen to the red rail, and a black wire from pin seven to the blue rail.",
     "start": 15.342,
     "dur": 14.351,
     "speech": 13.801
    },
    {
     "id": "w3",
     "text": "Step three: inputs A and B. Wire switch one, that's A, to XOR pin one. Wire switch two, that's B, to XOR pin two.",
     "start": 29.692,
     "dur": 10.194,
     "speech": 9.644
    },
    {
     "id": "w4",
     "text": "A and B also feed the first AND gate. So add two jumpers: from the XOR pin one strip to AND pin one, and from the XOR pin two strip to AND pin two. Remember: any hole in the same strip is the same connection.",
     "start": 39.886,
     "dur": 14.501,
     "speech": 13.951
    },
    {
     "id": "w5",
     "text": "Step four: the Sum chain. A short jumper from XOR pin three to XOR pin four. Then wire switch three, Carry in, to XOR pin five. XOR pin six is now the Sum.",
     "start": 54.388,
     "dur": 13.199,
     "speech": 12.649
    },
    {
     "id": "w6",
     "text": "Step five: the second AND gate. Wire XOR pin three to AND pin four. And wire Carry in, from the XOR pin five strip, to AND pin five.",
     "start": 67.587,
     "dur": 10.949,
     "speech": 10.399
    },
    {
     "id": "w7",
     "text": "Step six: the OR gate. Wire AND pin three to OR pin one, and AND pin six to OR pin two. OR pin three is now the Carry out.",
     "start": 78.536,
     "dur": 10,
     "speech": 9.307
    },
    {
     "id": "w8",
     "text": "Step seven: the lights. Choose two LEDs next to each other. Wire OR pin three to the left one: that's Carry out. Wire XOR pin six to the right one: that's Sum. Now the two lights read like a binary number.",
     "start": 88.536,
     "dur": 15.171,
     "speech": 14.621
    },
    {
     "id": "w9",
     "text": "That's every wire. Twenty in total: eight for power, and twelve for signals. Before switching on, check each one against the list.",
     "start": 103.707,
     "dur": 8.871,
     "speech": 8.321
    }
   ]
  },
  {
   "id": "test",
   "title": "Power on and test",
   "start": 618.79,
   "dur": 41.487,
   "cues": [
    {
     "id": "x1",
     "text": "Switch the kit on, and test all eight combinations. Before each flip, predict the lights with the count rule. Odd count: Sum. Two or more: Carry.",
     "start": 0.9,
     "dur": 10.587,
     "speech": 10.037
    },
    {
     "id": "x2",
     "text": "Watch the glowing wires. They carry five volts, a one. Follow any bright path, and you can see each gate making its decision.",
     "start": 11.487,
     "dur": 30,
     "speech": 8.367
    }
   ]
  },
  {
   "id": "debug",
   "title": "If it doesn't work",
   "start": 660.277,
   "dur": 48.692,
   "cues": [
    {
     "id": "e1",
     "text": "If something is wrong, don't worry. Check these in order.",
     "start": 0.9,
     "dur": 4.182,
     "speech": 3.632
    },
    {
     "id": "e2",
     "text": "Nothing lights at all? Check that every chip has its power wires on pin fourteen and pin seven, that the rails are bridged, and that the kit is on.",
     "start": 5.082,
     "dur": 9.256,
     "speech": 8.706
    },
    {
     "id": "e3",
     "text": "A chip gets hot? It's probably in backwards. Switch off right away, and check the notch.",
     "start": 14.338,
     "dur": 6.792,
     "speech": 6.242
    },
    {
     "id": "e4",
     "text": "Sum is right but Carry is wrong, or the other way round? Test one gate at a time. Move an LED wire onto a gate's output, pin three or pin six, and check it against that gate's rule.",
     "start": 21.13,
     "dur": 12.087,
     "speech": 11.537
    },
    {
     "id": "e5",
     "text": "An output stuck on? An input that isn't connected to anything acts like a one on L S chips. Look for a wire in the wrong strip. And if you use H C chips, tie the unused inputs, pins nine, ten, twelve and thirteen, to ground.",
     "start": 33.217,
     "dur": 15.475,
     "speech": 14.925
    }
   ]
  },
  {
   "id": "recap",
   "title": "Recap",
   "start": 708.969,
   "dur": 32.141,
   "cues": [
    {
     "id": "z1",
     "text": "Let's recap. A full adder adds one column of binary: A, B, and a carry coming in.",
     "start": 0.9,
     "dur": 6.771,
     "speech": 6.221
    },
    {
     "id": "z2",
     "text": "It counts the ones. Sum is on when the count is odd: two XOR gates. Carry is on when the count is two or more: A AND B, or Carry in AND the XOR, joined by an OR.",
     "start": 7.671,
     "dur": 12.47,
     "speech": 11.92
    },
    {
     "id": "z3",
     "text": "Chain four of them, each Carry out feeding the next Carry in, and you can add two four bit numbers. That's how real computers add. And you just built the first column yourself.",
     "start": 20.141,
     "dur": 12,
     "speech": 10.167
    }
   ]
  }
 ]
};
