# gesturecontrol-projector

### TODO:
 - [x] Make the overlay window work in its own thread non-blocking so that inputs from the camera get processed even when the overlay window is rendering
 - [x] refractor perform_onscreen_actions.py so that it actually ues the new cool wonderful amazing reworked filterapp.py (I'm excited!)
 - [x] TEST Make a more robust overlay window for rendering the User actions
 - [x] TEST Make sure the overlay circles aren't shown when the hands are ouside of the screen
 - [ ] Make sure overlaywindow never "blacks out" (high prio)
 - [ ] Make the detection of both hands better, as the programm gets slow as soon as 2 hands are visible
 - [ ]idea: make sure the hand detection happens in a second threat/process - it always instantly grabs everything from the camera, maybe theres even a way to make the hand detection run fully on the gpu


 - [ ] Implement a presentation mode
 - [ ] For presenation mode it might make sense to use selenium, or to get it going with simulating "next" and "previous" buttons usually used for music control
 - [ ] Make sure whole application closes when Overlaywindow gets closed by User
 - [ ] Remove pygame welcome message
 - [ ] make sure the Oherlay makes its first call for tranparency during init, so that it's ready when we enter main loop and does not need to be created only then
 - [ ] Update the README.md to something actually useful