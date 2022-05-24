SynthDef("scTwitterBot", {
	var sig = $synth_def;

	Out.ar(0,
		sig.tanh*0.95,
	)
}).writeDefFile;


x = [
[0.0, [ \s_new, \scTwitterBot, 1000, 0, 0]],
[$duration, [\c_set, 0, 0]]
];

Score.write(x, "$osc_path");

0.exit;
