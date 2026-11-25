-- Render <name>.docx to <name>.pdf with Microsoft Word (the same route as r1119-r1124; recovered 2026-11-25 from the
-- 11-20 session, which kept it only in the scratchpad). Word is sandboxed, so the docx is copied into its container
-- folder first and the PDF copied back out:
--   cp X.docx ~/Library/Containers/com.microsoft.Word/Data/ && osascript word_render.applescript X
-- Opens and closes only that one document, without saving it.
on run argv
	set nm to item 1 of argv
	set base to "/Users/MarcusMarcus/Library/Containers/com.microsoft.Word/Data/"
	set src to POSIX file (base & nm & ".docx")
	tell application "Microsoft Word"
		open src
		delay 3
		set d to document (nm & ".docx")
		set n to compute statistics d statistic statistic pages
		save as d file name (base & nm & ".pdf") file format format PDF
		close d saving no
	end tell
	return nm & " pages: " & n
end run
