form "Parameters"
    comment Specify the ID of the sound file you wish to have analyzed
    positive File_id 1
    comment How many formants per vowel
    positive Formants 3
endform

clearinfo
folder$ = chooseFolder$: "Choose a folder: "
file_name$ = "\script_output.txt"
file_path$ = folder$ + file_name$
appendInfoLine: file_path$ 
# Clear old file
writeFile: file_path$, ""
selectObject: "TextGrid modified_file"

getVowel = 0
number_of_intervals = Get number of intervals: 1
for i to number_of_intervals
	label$ = Get label of interval: 1, i
	start_time = Get start time of interval: 1, i
	end_time = Get end time of interval: 1, i
	duration = end_time - start_time
	if getVowel == 1
		appendFile: file_path$, "Vowel: "
		appendFileLine: file_path$, duration
		getVowel = 0
        @writeVowelFormants: start_time, end_time
		appendFileLine: file_path$
        selectObject: "TextGrid modified_file"
	endif
	if label$ == "t"	
		appendFileLine: file_path$, "Release: ", duration
		getVowel = 1
		@writeSpectralData: start_time, end_time 
		@writeFricativeFormant: 
        selectObject: "TextGrid modified_file"
	endif
	if label$ == "tc"
		appendFile: file_path$, "Closure: "
		appendFileLine: file_path$, duration
	endif
endfor

procedure writeSpectralData: .start, .end
	selectObject: file_id
	sound_part = Extract part: .start, .end, "rectangular", 1.0, 0
	spectrum = To Spectrum: 1
	cog = Get centre of gravity: 2
	skew = Get skewness: 2
	sd = Get standard deviation: 2
    appendFileLine: file_path$, "Center of Gravity: ", cog
	appendFileLine: file_path$, "Skewness: ", skew
	appendFileLine: file_path$, "Standard Deviation: ", sd
	removeObject: spectrum
endproc

procedure writeVowelFormants: .start, .end
    selectObject: file_id
    sound_part = Extract part: .start, .end, "rectangular", 1.0, 0
    # TODO: Change third argument for males vs females
    formant = To Formant (burg): 0.0, 5.0, 5500.0, 0.025, 50.0
    for j to formants
        formant_value_20ms = Get value at time: j, 0.02, "hertz", "linear"
        formant_value_40ms = Get value at time: j, 0.04, "hertz", "linear"
        appendFileLine: file_path$, "F", j, " 20ms: ", formant_value_20ms
        appendFileLine: file_path$, "F", j, " 40ms: ", formant_value_40ms
    endfor
    removeObject: sound_part, formant
endproc

procedure writeFricativeFormant:
    selectObject: sound_part
    formant = To Formant (burg): 0.0, 5.0, 5500.0, 0.025, 50.0
    fricative_formant_mean = Get mean: 3, 0.0, 0.0, "hertz"
    appendFileLine: file_path$, "Mean Fricative F3: ", fricative_formant_mean
    removeObject: sound_part, formant
endproc