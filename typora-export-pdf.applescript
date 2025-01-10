# For Typora on MacOS
on run {inputFile}
    tell application "Typora"
        activate
        open inputFile
        tell application "System Events"

            -- Wait for Typora window to be ready
            delay 1
            repeat until (exists window 1 of process "Typora")
                delay 0.1
            end repeat
            
            -- Export to PDF
            delay 1
            keystroke "p" using {command down, control down}
            
            -- Wait for save dialog
            delay 1
            repeat until (exists sheet 1 of window 1 of process "Typora")
                delay 0.1
            end repeat
            
            -- Confirm save
            delay 1
            keystroke return
            
            -- Wait until save dialog disappears
            delay 1
            repeat until not (exists sheet 1 of window 1 of process "Typora")
                delay 0.1
            end repeat
        end tell
        
        close front window -- Close the current file
    end tell
end run