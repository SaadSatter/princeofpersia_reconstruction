-- Export a deck to PDF and one PNG per slide with Keynote.
-- usage: osascript presentation/export_keynote.applescript /abs/in.pptx /abs/out.pdf /abs/slides_dir
-- Keynote cannot import the notes master python-pptx writes, so export the copy built with
-- NO_NOTES=1 (identical slides, no speaker notes); the notes live in the shipped .pptx.
on run argv
	set inFile to POSIX file (item 1 of argv)
	set pdfFile to POSIX file (item 2 of argv)
	set imgDir to POSIX file (item 3 of argv)
	tell application "Keynote"
		set theDoc to open inFile
		export theDoc to pdfFile as PDF
		export theDoc to imgDir as slide images with properties {image format:PNG}
		close theDoc saving no
	end tell
end run
